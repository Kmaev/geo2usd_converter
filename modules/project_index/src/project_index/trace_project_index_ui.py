import json
import os
import re
import sys
from importlib import reload

from PySide6 import QtWidgets, QtCore, QtGui  # This should run on PySide2 add PySide2 package to REZ env

import utils

reload(utils)


class TraceProjectIndex(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(TraceProjectIndex, self).__init__(parent=parent)
        # Set tool utils attr

        self.resize(900, 700)
        self.undo_stack = []
        self._rename_cache = None
        self.setWindowTitle('Trace Project Index v0.1.6')

        # Get env vars
        style_folder = os.environ.get("STYLE_KPROJECT_INDEX")
        self.project_index_path = os.getenv("PROJECTS_INDEX_PATH")
        self.show_root = os.getenv("PR_SHOW_ROOT")

        self.central_widget = QtWidgets.QWidget()
        self.central_layout = QtWidgets.QVBoxLayout(self.central_widget)
        self.setCentralWidget(self.central_widget)

        # Top Button Layout
        self.top_button_layout = QtWidgets.QHBoxLayout()
        self.top_button_layout.addStretch()
        self.central_layout.addLayout(self.top_button_layout)

        self.add_button = QtWidgets.QPushButton("Add")
        self.add_button.setFixedSize(124, 24)
        self.top_button_layout.addWidget(self.add_button)

        self.delete_button = QtWidgets.QPushButton("Delete")
        self.delete_button.setFixedSize(124, 24)
        self.top_button_layout.addWidget(self.delete_button)

        self.info_button = QtWidgets.QPushButton("?")
        self.info_button.setFixedSize(24, 24)
        self.info_button.setToolTip("Click for help")
        self.top_button_layout.addWidget(self.info_button)

        # Projects Edit
        self.edit_label = QtWidgets.QLabel("Project Hierarchy Editor")
        self.central_layout.addWidget(self.edit_label)

        self.tree_widget = MyTreeWidget()
        self.tree_widget.setHeaderLabels(["Projects:"])
        self.central_layout.addWidget(self.tree_widget)
        self.tree_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tree_widget.setFocus()
        self.max_tree_depth = 3

        # Tasks, DCC Edit and folder structure creation
        self.dcc_label = QtWidgets.QLabel("Software Folder Templates (space-separated)")
        self.central_layout.addWidget(self.dcc_label)

        self.added_task_subfolders_check = QtWidgets.QCheckBox("Create software-based subfolders under each Task")
        self.central_layout.addWidget(self.added_task_subfolders_check)

        self.include_software = QtWidgets.QLineEdit()
        self.include_software.setEnabled(False)
        self.include_software.setPlaceholderText(
            'Type space-separated list of software to include e.g. houdini blender unreal')
        self.central_layout.addWidget(self.include_software)

        self.create_project_line_edit = QtWidgets.QLineEdit()
        self.create_project_line_edit.setPlaceholderText(
            'Retype project name to confirm creation or update')
        self.central_layout.addWidget(self.create_project_line_edit)

        self.create_folder_structure_btn = QtWidgets.QPushButton("Create Folder Structure")
        self.central_layout.addWidget(self.create_folder_structure_btn)
        # Load and set style
        style_file = os.path.join(style_folder, "style.qss")
        with open(style_file, 'r') as f:
            style = f.read()

        self.setStyleSheet(style)

        if self.parent():
            self.parent().setStyleSheet(self.parent().styleSheet())
        # ===============================================================================================================
        # Functions executed on init
        self.populate_tree()

        # ===============================================================================================================
        # Widget signal connections
        self.info_button.clicked.connect(self.show_info_popup)

        self.add_button.clicked.connect(self.add_tree_item)
        self.delete_button.clicked.connect(self.delete_tree_item)
        self.tree_widget.customContextMenuRequested.connect(self.open_menu)
        self.tree_widget.delete_key_pressed.connect(self.delete_tree_item)

        self.tree_widget.itemChanged.connect(self.track_rename)
        self.tree_widget.itemChanged.connect(self.validate_item_name)

        self.tree_widget.itemSelectionChanged.connect(self.cache_selected_item_name)

        self.added_task_subfolders_check.stateChanged.connect(self.on_add_task_checked)

        self.create_folder_structure_btn.clicked.connect(self.create_folder_structure)

        # Shortcuts signal connections
        self.undo_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Z"), self)
        self.undo_shortcut.activated.connect(self.undo_action)

        self.add_shortcut = QtGui.QShortcut(QtGui.QKeySequence("N"), self)
        self.add_shortcut.activated.connect(self.add_tree_item)

    def on_add_task_checked(self):
        """
        Enables or disables the software input field based on the 'Add Tasks Subfolder' checkbox.
        Disables editing if the checkbox is unchecked.
        """
        self.include_software.setEnabled(self.added_task_subfolders_check.isChecked())

    def _tree_item(self, name, parent, removable=False):
        """
        Defines a QTreeWidgetItem and adds it to the parent.
        """
        _parent = parent
        count = 1

        while _parent.parent():
            count += 1
            _parent = _parent.parent()

        if count > self.max_tree_depth:
            return

        item = QtWidgets.QTreeWidgetItem(parent)
        item.setText(0, name)
        metadata = {"removable": removable,
                    "type": "task" if count == 2 else "core"}
        item.setData(0, QtCore.Qt.UserRole, metadata)
        if removable:
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
        else:
            item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
        return item

    def populate_tree(self):
        """
        Executed on init. Populates the tree widget with existing projects from the project index JSON file.
        """
        if not os.path.isfile(self.project_index_path):
            read = {}
        else:
            with open(self.project_index_path, "r") as read_file:
                read = json.load(read_file)

        root = self.tree_widget.invisibleRootItem()

        for project_name, groups in read.items():
            project = self._tree_item(project_name, root)

            for group, items in groups['groups'].items():
                group = self._tree_item(group, project)

                for item, tasks in items['items'].items():
                    item = self._tree_item(item, group)
                    for task, _ in tasks['tasks'].items():
                        self._tree_item(task, item)

    def get_selection(self):
        """
        Returns the currently selected item.
        If nothing is selected, returns the invisible root item.
        """
        selected = self.tree_widget.selectedItems()
        if selected:
            return selected[0]
        else:
            return self.tree_widget.invisibleRootItem()

    def open_menu(self, position):
        """
        Opens the right-click context menu for the selected tree item.
        """
        item = self.tree_widget.itemAt(position)
        menu = QtWidgets.QMenu(self)

        if item:
            add_action = menu.addAction("Add \t\t(N)")
            add_action.triggered.connect(self.add_tree_item)

            delete_action = menu.addAction("Delete")
            delete_action.triggered.connect(self.delete_tree_item)

        else:
            add_action = menu.addAction("Add New Project")
            add_action.triggered.connect(self.add_tree_item)
        menu.exec_(self.tree_widget.viewport().mapToGlobal(position))

    def add_tree_item(self):
        """
        Handles the logic for adding a new tree item.
        """
        parent = self.get_selection()
        item = self._tree_item("Untitled", parent, removable=True)

        if not item:
            message = 'Template supports only \nProject->Group->Item->Task hierarchy'
            QtWidgets.QMessageBox.critical(self, 'Error', message)
            raise RuntimeError(message)

        self.tree_widget.expandItem(parent)
        item.setSelected(True)
        parent.setSelected(False)
        self.tree_widget.editItem(item)

        self.undo_stack.append(('add', item, parent))

    def delete_tree_item(self):
        """
        Handles the logic for deleting a tree item.
        """
        selected = self.tree_widget.selectedItems()
        if selected:
            item = selected[0]
            metadata = item.data(0, QtCore.Qt.UserRole)
            removable = metadata.get("removable")
            if not removable:
                QtWidgets.QMessageBox.information(
                    self,
                    "Non-removable Item",
                    "This name represents a system-defined folder and cannot be deleted."
                    "Please contact support for manual override or structural changes."
                )
                return
            parent = item.parent()

            # Save undo info
            index = parent.indexOfChild(item) if parent else self.tree_widget.indexOfTopLevelItem(item)
            self.undo_stack.append(('delete', item.clone(), parent, index))

            if parent:
                parent.removeChild(item)
            else:
                index = self.tree_widget.indexOfTopLevelItem(item)
                self.tree_widget.takeTopLevelItem(index)

    def validate_item_name(self, item):
        """
        Validates the item's name:
        - Sets to 'Untitled' if empty
        - Replaces spaces with underscores
        """
        if item.text(0) == "":
            item.setText(0, "Untitled")
        elif " " in item.text(0):
            new_text = item.text(0).replace(" ", "_")
            item.setText(0, new_text)

    def update_project_index(self):
        """
        Updates the project index JSON file based on the current tree widget structure.
        Executed when 'Create Folder Structure' is pressed.
        """
        index = {}
        root = self.tree_widget.invisibleRootItem()
        self._walk(root, index, -1)
        index = index['children']

        dirname = os.path.dirname(self.project_index_path)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)

        with open(self.project_index_path, 'w') as output_file:
            json.dump(index, output_file, indent=4)

    def _walk(self, parent, index, level):
        """
        Recursively traverses the tree and builds a nested dictionary
        representing groups, items, and tasks.
        """
        labels = ['groups', 'items', 'tasks']

        if level == -1:
            label = 'children'
        else:
            try:
                label = labels[level]
            except IndexError:
                return
        index[label] = {}

        for row in range(parent.childCount()):
            child_item = parent.child(row)
            name = child_item.text(0)
            index[label][name] = {}
            self._walk(child_item, index[label][name], level + 1)

    def create_folder_structure(self):
        """
        Handles logic for the 'Create Folder Structure' button.
        Validates environment variables and user input, creates folders on disk,
        and updates the project index.
        """
        if not self.show_root:
            QtWidgets.QMessageBox.critical(self, "Error", "Environment variable 'PR_SHOW_ROOT' is not set.")
            return

        input_name = self.create_project_line_edit.text()
        if not input_name:
            QtWidgets.QMessageBox.critical(self, "Error", "Please enter a project name to create or update.")
            return

        root_item = self.tree_widget.invisibleRootItem()
        root = None

        for i in range(root_item.childCount()):
            item = root_item.child(i)
            if item.text(0) == input_name:
                root = item
                break

        if not root:
            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                f"The project name '{input_name}' doesn't match any defined projects.\n\n"
                "Please double-check the spelling or create the project first."
            )
            return

        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirm Folder Creation",
            f"This action will create or update the folder structure for '{root.text(0)}'. Do you wish to continue?"
            f"Please note: this action cannot be undone.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )

        if reply != QtWidgets.QMessageBox.Yes:
            return

        show_folder_path = os.path.join(self.show_root, root.text(0))
        if not os.path.isdir(self.show_root):
            os.makedirs(self.show_root)
        if self.added_task_subfolders_check.isChecked():
            self.check_dcc_name()
        self._create_folders_recursive(root, show_folder_path)

        self.update_project_index()

        self._reset_ui_state()
        self.tree_widget.clear()
        self.populate_tree()

    def _create_folders_recursive(self, item, current_path):
        """
        Recursively creates folders based on the tree widget structure.
        Also creates software-specific subfolders for task nodes.
        """
        for i in range(item.childCount()):
            child = item.child(i)
            folder_name = child.text(0)
            metadata = item.data(0, QtCore.Qt.UserRole)
            item_type = metadata.get("type")

            folder_path = os.path.join(current_path, folder_name)
            if item_type == "task" and self.added_task_subfolders_check.isChecked():
                dcc_list = self.include_software.text().split(" ")
                for dcc_name in dcc_list:
                    utils.create_dcc_folder_structure(dcc_name, str(folder_path))

            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            self._create_folders_recursive(child, folder_path)

    def _reset_ui_state(self):
        """
        Resets the UI elements and internal state after folder creation.
        Clears input fields, unchecks the task checkbox, and resets
        undo history and rename tracking.
        """
        self.include_software.setText("")
        self.create_project_line_edit.setText("")
        self.added_task_subfolders_check.setChecked(False)
        self.undo_stack = []
        self._rename_cache = None

    def check_dcc_name(self):
        """
        Checks DCC names for typos and suggestions.
        Confirms changes with the user and separates valid and skipped DCCs.
        """
        dcc_orig_user_input = self.include_software.text().split(" ")
        _dcc_list = [re.sub(r'[^a-zA-Z0-9]', '', item) for item in dcc_orig_user_input]

        templ = utils.get_dcc_template()
        skipped_dcc = []
        checked_dcc_list = []
        confirmed_suggestions = []

        for _dcc in _dcc_list:
            suggestion = utils.dcc_template_check(_dcc, templ)
            if suggestion:
                if suggestion not in confirmed_suggestions:
                    reply = QtWidgets.QMessageBox.question(
                        self,
                        "Confirm Folder Creation",
                        f"DCC {_dcc} is not found Did you mean '{suggestion}'",
                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
                    )

                    if reply != QtWidgets.QMessageBox.Yes:
                        continue
                    else:
                        dcc_name = suggestion
                        confirmed_suggestions.append(suggestion)
                else:
                    dcc_name = suggestion

            else:
                dcc_name = _dcc

            if dcc_name not in templ.keys() and dcc_name not in skipped_dcc:
                skipped_dcc.append(dcc_name)
            else:
                checked_dcc_list.append(dcc_name)
        self.include_software.setText(" ".join(checked_dcc_list))
        if skipped_dcc:
            QtWidgets.QMessageBox.information(
                self,
                "Template Not Found",
                "The following DCC(s) will be skipped during folder creation because their "
                "templates were not found:\n\n" + "\n".join(
                    skipped_dcc))

    # Ctrl + Z Logic
    def undo_action(self):
        """
        Handles undo logic for add, delete, and rename actions.
        Triggered by Ctrl+Z.
        """
        if not self.undo_stack:
            return

        action = self.undo_stack.pop()

        if action[0] == 'add':
            _, item, parent = action
            if parent:
                parent.removeChild(item)
            else:
                index = self.tree_widget.indexOfTopLevelItem(item)
                self.tree_widget.takeTopLevelItem(index)

        elif action[0] == 'delete':
            _, item, parent, index = action
            if parent:
                parent.insertChild(index, item)
            else:
                self.tree_widget.insertTopLevelItem(index, item)
        elif action[0] == 'rename':
            _, item, old_name, new_name = action
            item.setText(0, old_name)

    def cache_selected_item_name(self):
        """
        Stores the current item's name to track renames.
        """
        selected = self.tree_widget.selectedItems()
        if selected:
            self._rename_cache = selected[0].text(0)
        else:
            self._rename_cache = None

    def track_rename(self, item, column):
        """
        Tracks rename actions and adds them to the undo stack.
        """
        old_name = self._rename_cache
        new_name = item.text(column)

        if old_name and old_name != new_name:
            self.undo_stack.append(('rename', item, old_name, new_name))

        self._rename_cache = None

    def show_info_popup(self):
        """
        Displays the help popup window when the info button is clicked.
        """
        QtWidgets.QMessageBox.information(
            self,
            "How to Use",
            "• Press 'N' to create a new project or add a new name. or right-click and choose 'Add'.\n\n"
            "• You can delete items using the 'Delete' key or by right-clicking and choosing 'Delete'.\n\n"
            "• After finishing your edits, type the project name to confirm the project you want to create or update.\n\n"
            "• Click the 'Create Folder Structure' button to write changes to disk and update the project index.\n\n"
            "• ⚠️ Please note: Once you click 'Create Folder Structure', the operation is final and cannot be undone.  "
            "You may continue adding items, but system-defined folders created during this process cannot be deleted. "
            "For structural modifications, please contact support.\n\n "
            "• The folder structure follows this template:\n\n"
            "  Project → Group → Item → Task (optional)\n\n"
            "  - 'Group' might represent a sequence (e.g., Seq01, Seq02) or a folder that contains all assets (e.g., 'Assets').\n"
            "    'Item' would be the shot or asset name (e.g., 'shot_0010' or 'city_building_01').\n\n"
            "• You can see an example of the recommended structure at the top of the window."
        )


class MyTreeWidget(QtWidgets.QTreeWidget):
    delete_key_pressed = QtCore.Signal()

    def mousePressEvent(self, event):
        """
        Clears selection if user clicks on empty space in the tree.
        """
        if not self.indexAt(event.position().toPoint()).isValid():
            self.selectionModel().clear()
        return super(MyTreeWidget, self).mousePressEvent(event)

    def keyPressEvent(self, event):
        """
        Emits a signal when Delete or Backspace is pressed.
        """
        if event.key() in (QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace):
            self.delete_key_pressed.emit()
        else:
            super(MyTreeWidget, self).keyPressEvent(event)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = TraceProjectIndex()
    w.show()
    sys.exit(app.exec())
