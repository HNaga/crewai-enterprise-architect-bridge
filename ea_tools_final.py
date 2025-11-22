import win32com.client
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import json
import time
import os
import traceback

# =============================================================================
# INPUT SCHEMA
# =============================================================================
class EARequestSchema(BaseModel):
    json_structure: str = Field(..., description="JSON string containing the 'action', 'package_name', 'elements', etc.")
    project_path: str = Field(..., description="Absolute path to the .eapx or .qea file.")

# =============================================================================
# THE MAIN TOOL CLASS
# =============================================================================
class EnterpriseArchitectToolFinal(BaseTool):
    name: str = "EA Universal Builder"
    description: str = (
        "Interact with Enterprise Architect. Can 'build' models (Packages, Diagrams, Elements) "
        "or 'report' (generate documentation). Expects JSON input."
    )
    args_schema: type[BaseModel] = EARequestSchema

    def _connect_to_ea(self, project_path):
        """Helper to establish connection to EA"""
        ea_repo = None
        try:
            # Attempt 1: Hook into existing open window
            ea_repo = win32com.client.GetActiveObject("EA.Repository")
        except:
            # Attempt 2: Launch new instance
            try:
                ea_repo = win32com.client.Dispatch("EA.Repository")
                try: 
                    ea_repo.ShowWindow(1) # Make visible
                except: pass 
            except Exception as e:
                raise Exception(f"Could not launch EA. Is it installed? Error: {e}")

        # Open File if needed
        try:
            # Simple check to see if the correct file is open, otherwise open it
            if project_path.lower() not in ea_repo.ConnectionString.lower():
                ea_repo.OpenFile(project_path)
        except:
            # If nothing is open, open the file
            ea_repo.OpenFile(project_path)
            
        return ea_repo

    def _run(self, json_structure: str, project_path: str) -> str:
        try:
            # 1. PARSE JSON
            try:
                data = json.loads(json_structure)
            except json.JSONDecodeError:
                return "❌ JSON Error: Input was not valid JSON."

            # Determine Action: "build" (default) or "report"
            action = data.get('action', 'build').lower()
            package_name = data.get('package_name', 'AI_Gen')

            # 2. CONNECT TO EA
            try:
                ea_repo = self._connect_to_ea(project_path)
            except Exception as e:
                return f"❌ Connection Error: {str(e)}"

            if ea_repo.Models.Count == 0:
                return "❌ Error: Project is empty. Create a root model manually first."
            
            model_root = ea_repo.Models.GetAt(0)

            # 3. FIND/CREATE TARGET PACKAGE
            package = None
            for pkg in model_root.Packages:
                if pkg.Name == package_name:
                    package = pkg
                    break
            
            if not package:
                if action == 'report':
                    return f"❌ Cannot generate report: Package '{package_name}' not found."
                # If building, create it
                package = model_root.Packages.AddNew(package_name, "Package")
                package.Update()
                model_root.Packages.Refresh()

            # =========================================================
            # ACTION: GENERATE REPORT
            # =========================================================
            if action == 'report':
                output_file = data.get('output_file', r'C:\Temp\Report.rtf')
                template = data.get('template', 'Model Report') # Use 'Model Report' or your custom 'Professional_SAD'
                
                try:
                    project_int = ea_repo.GetProjectInterface()
                    # RunReport: PackageGUID, TemplateName, FileName, Format (RTF)
                    project_int.RunReport(package.PackageGUID, template, output_file)
                    return f"✅ Report generated successfully at: {output_file}"
                except Exception as e:
                    return f"❌ Report Generation Failed: {e}"

            # =========================================================
            # ACTION: BUILD MODEL
            # =========================================================
            
            elements = data.get('elements', [])
            connectors = data.get('connectors', [])
            diag_name = data.get('diagram_name', "Architecture Diagram")

            # A. Get/Create Diagram
            diagram = None
            for d in package.Diagrams:
                if d.Name == diag_name:
                    diagram = d
                    break
            if not diagram:
                diagram = package.Diagrams.AddNew(diag_name, data.get('diagram_type', 'Logical'))
                diagram.Update()
                package.Diagrams.Refresh()

            print(f"🚀 Building Package: {package_name}")

            # B. PHASE 1: DATABASE CREATION (Data Entry)
            created_names = []
            
            for el in elements:
                name = el.get('name', 'Unnamed')
                el_type = el.get('type', 'Class')

                # --- Auto-Fix Types ---
                # Agents often hallucinate types; we map them to valid EA types
                if "Story" in el_type: 
                    el_type = "Requirement"
                    el.setdefault('stereotype', 'User Story')
                elif "Table" in el_type: 
                    el_type = "Class"
                    el.setdefault('stereotype', 'table')
                elif "Screen" in el_type:
                    el_type = "Class"
                    el.setdefault('stereotype', 'screen')

                # Create Element
                try:
                    ea_el = package.Elements.AddNew(name, el_type)
                    ea_el.Notes = el.get('description', "")
                    if 'stereotype' in el: 
                        ea_el.Stereotype = el['stereotype']
                    ea_el.Update() # Initial save to get ID

                    # Add Attributes (for Classes/Tables)
                    for attr in el.get('attributes', []):
                        try:
                            # Handle string "id" or dict {"name": "id", "type": "int"}
                            aname = attr if isinstance(attr, str) else attr.get('name')
                            atype = "string" if isinstance(attr, str) else attr.get('type', "string")
                            
                            new_attr = ea_el.Attributes.AddNew(aname, atype)
                            if not isinstance(attr, str) and attr.get('is_pk'):
                                new_attr.IsOrdered = True # Common way to mark PK in EA
                            new_attr.Update()
                        except: pass

                    # Add Scenarios (for Use Cases)
                    for scen in el.get('scenarios', []):
                        try:
                            s = ea_el.Scenarios.AddNew(scen['name'], "Basic Path")
                            # EA stores steps in XML or Notes depending on version. 
                            # Storing in Notes is safest for visibility.
                            steps = "\n".join([f"{i+1}. {x}" for i,x in enumerate(scen.get('steps', []))])
                            s.Notes = steps
                            s.Update()
                        except: pass
                    
                    ea_el.Update() # Final save
                    created_names.append(name)
                    
                except Exception as e:
                    print(f"⚠️ Failed to create {name}: {e}")

            package.Elements.Refresh() # CRITICAL: Commit to DB before drawing

            # C. PHASE 2: VISUALIZATION (Diagram Layout)
            # We use Negative Y-Axis coordinates to ensure visibility
            left = 20
            top = -20 
            width = 120
            height = 70
            gap_x = 50
            gap_y = 50
            
            element_map = {} # Cache for connectors

            for name in created_names:
                try:
                    ea_el = package.Elements.GetByName(name)
                    element_map[name] = ea_el
                    
                    if ea_el.ElementID > 0:
                        # Check if already on diagram
                        exists = False
                        for obj in diagram.DiagramObjects:
                            if obj.ElementID == ea_el.ElementID:
                                exists = True
                                break
                        
                        if not exists:
                            # Calculate Bottom/Right
                            right = left + width
                            bottom = top - height 
                            
                            # EA Position String
                            pos = f"l={left};r={right};t={top};b={bottom}"
                            
                            d_obj = diagram.DiagramObjects.AddNew(pos, "")
                            d_obj.ElementID = ea_el.ElementID
                            d_obj.Update()
                            
                            # Move Grid logic
                            left += (width + gap_x)
                            if left > 600: # Wrap to next row
                                left = 20
                                top -= (height + gap_y)
                except: pass

            diagram.DiagramObjects.Refresh()

            # D. PHASE 3: CONNECTORS
            for link in connectors:
                try:
                    src = element_map.get(link.get('source'))
                    tgt = element_map.get(link.get('target'))
                    
                    if src and tgt:
                        # Check for existing link to avoid duplicates
                        exists = False
                        for conn in src.Connectors:
                            if conn.SupplierID == tgt.ElementID:
                                exists = True
                                break
                        
                        if not exists:
                            c = src.Connectors.AddNew(link.get('label', ""), link.get('type', 'Association'))
                            c.SupplierID = tgt.ElementID
                            if 'stereotype' in link: c.Stereotype = link['stereotype']
                            c.Update()
                except: pass

            # E. PHASE 4: AUTO LAYOUT
            try:
                project_int = ea_repo.GetProjectInterface()
                # LayoutDiagramEx: GUID, Style(0), Iterations(4), LayerSpace(20), ColSpace(20), Save(True)
                project_int.LayoutDiagramEx(diagram.DiagramGUID, 0, 4, 20, 20, True)
                ea_repo.ReloadDiagram(diagram.DiagramID)
            except:
                pass

            # F. OPTIONAL CLEANUP
            # ea_repo.Exit() # Uncomment if you want EA to close automatically

            return f"✅ Success! Package '{package_name}' built with {len(created_names)} elements."

        except Exception as e:
            # traceback.print_exc() # Useful for debugging
            return f"❌ Critical Tool Error: {str(e)}"