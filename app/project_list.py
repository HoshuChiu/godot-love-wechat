from dataclasses import dataclass, field
from typing import Callable, Dict, List
from nicegui import ui, app, run
from app.utils import parse_godot_project
from app.stroge import Storge
from PIL import Image
import webview
import uuid
import os

@dataclass
class ProjectManager:
    on_change: Callable
    stroge: Storge = field(default_factory=Storge)
    projects: List[Dict] = field(default_factory=list)
    search = ""

    async def add(self, project):
        self.projects.append(project)
        await run.io_bound(self.stroge.save, "projects.json", self.projects)
        self.on_change()

    async def remove(self, project):
        self.projects.remove(project)
        await run.io_bound(self.stroge.save, "projects.json", self.projects)
        self.on_change()

    def init(self):
        projects = self.stroge.get("projects.json")
        if projects:
            self.projects = projects



@ui.refreshable
def project_card():
    with ui.grid(columns=3).classes("w-full p-4"):
        for project in project_manager.projects:
            if project["name"].startswith(project_manager.search):
                with ui.card().tight():
                    with ui.image(Image.open(project["icon"])):
                        with ui.column().classes("w-full absolute-bottom"):
                            ui.label(project["name"]).classes("text-h6")
                            ui.label(f"Version: {project["version"]}").classes("text-subtitle2")
                    with ui.card_section():
                        ui.label(project["description"]).classes("text-caption")
                    with ui.card_actions():
                        ui.button("转换", icon="swap_horiz", on_click=lambda: ui.navigate.to(f"/projects/{project["id"]}")).props("flat")
                        ui.button("删除", icon="delete", on_click=lambda: project_manager.remove(project)).props("flat")


project_manager = ProjectManager(on_change=project_card.refresh)

@ui.refreshable
def project_list():
    
    project_manager.init()

    async def import_project():
        file = await app.native.main_window.create_file_dialog(dialog_type=webview.FOLDER_DIALOG, allow_multiple=False, file_types=()) # type: ignore
        if not file:
            return
        folder = file[0]
        project = os.path.join(folder, "project.godot")
        project_data = await run.io_bound(parse_godot_project, project)
        application = project_data["application"]
        project = {
            "id": uuid.uuid4().hex, 
            "name": application.get("config/name", ""),
            "path": folder,
            "version": application.get("config/version", ""),
            "description": application.get("config/description", ""),
            "icon": (
                application.get("config/icon", "").split("//")[-1]
                if application.get("config/icon", "")
                else "icon.svg"
            ),
        }
        icon_path = os.path.join(folder, project["icon"])
        project["icon"] = icon_path 
        await project_manager.add(project)


    with ui.column(align_items="start").classes("w-full h-full p2"):
        with ui.row().classes("border-b pb-2 w-full"):
            ui.markdown("### 项目")
        with ui.row().classes("w-full pl-4 pr-4"):
            search_input = ui.input(placeholder="搜索", on_change=project_card.refresh).classes("w-64").props("outlined dense").bind_value(project_manager, "search")
            with search_input.add_slot("prepend"):
                ui.icon("search")
            ui.space()
            ui.button("导入", on_click=import_project)
        with ui.row().classes("w-full overflow-y-auto"):
            project_card()

    
