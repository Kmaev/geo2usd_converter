
from PySide6 import QtWidgets, QtCore, QtGui
import sys
import os
import json
#from kproject_index import res


class ProjectIndex(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(ProjectIndex, self).__init__(parent=parent)
        self.resize(800, 400)
        #style_folder = os.environ.get("STYLE_KPROJECT_INDEX")

        #self.setWindowIcon(QtGui.QIcon(os.path.join(style_folder, "images/logo/app_logo.png")))
        self.project_index_path = os.getenv("PROJECTS_INDEX_PATH")

        self.central_widget = QtWidgets.QWidget()
        self.central_layout = QtWidgets.QVBoxLayout(self.central_widget)
        self.setCentralWidget(self.central_widget)

        self.setWindowTitle('Project Index v0.1.6')

        self.tree_widget = MyTreeWidget()
        self.tree_widget.setHeaderLabels(["Projects:"])
        self.central_layout.addWidget(self.tree_widget)

        self.buttons_layout = QtWidgets.QHBoxLayout()
        self.central_layout.addLayout(self.buttons_layout)

        self.add_button = QtWidgets.QPushButton("Add")
        self.buttons_layout.addWidget(self.add_button)
        self.add_button.clicked.connect(self.addTreeItem)

        self.delete_button = QtWidgets.QPushButton("Delete")
        self.buttons_layout.addWidget(self.delete_button)
        self.delete_button.clicked.connect(self.deleteTreeItem)

        self.save_button = QtWidgets.QPushButton("Save")
        self.buttons_layout.addWidget(self.save_button)
        self.save_button.clicked.connect(self.getProjectIndex)
        self.populateTree()
        # self.getProjectIndex()
        # self.deleteLater()


        #style_file = os.path.join(style_folder, "style.qss")
        #with open(style_file, 'r') as f:
         #   style = f.read()

        #self.setStyleSheet(style)

        # if self.parent():
        #     self.parent().setStyleSheet(self.parent().styleSheet())

    def _tree_item(self, name, parent):

        _parent = parent
        count = 1

        while _parent.parent():
            count += 1
            _parent = _parent.parent()

        if count > 2:
            return

        item = QtWidgets.QTreeWidgetItem(parent)
        item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
        item.setText(0, name)
        return item

    def populateTree(self):

        if not os.path.isfile(self.project_index_path):
            read = {}
        else:
            with open(self.project_index_path, "r") as read_file:
                read = json.load(read_file)

        root = self.tree_widget.invisibleRootItem()

        for project_name, sequences in read.items():
            project = self._tree_item(project_name, root)

            for sequence, shots in sequences['sequences'].items():
                sequence = self._tree_item(sequence, project)

                for shot, _ in shots['shots'].items():
                    shot = self._tree_item(shot, sequence)

    def getSelection(self):
        selected = self.tree_widget.selectedItems()
        if selected:
            return selected[0]
        else:
            return self.tree_widget.invisibleRootItem()

    def addTreeItem(self):
        parent = self.getSelection()
        item = self._tree_item("Untitled", parent)
        if not item:
            message = 'This template supports only Project->Sequence->Shot hierarchy'
            QtWidgets.QMessageBox.critical(self, 'Error', message)
            raise RuntimeError(message)

        self.tree_widget.expandItem(parent)
        item.setSelected(True)
        parent.setSelected(False)

    def deleteTreeItem(self):
        selected = self.tree_widget.selectedItems()
        if selected:
            self.tree_widget.invisibleRootItem().removeChild(selected[0])
        else:
            print("No name was selected")

    def getProjectIndex(self):

        index = {}
        root = self.tree_widget.invisibleRootItem()
        self._walk(root, index, -1)
        index = index['children']

        dirname = os.path.dirname(self.project_index_path)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)

        with open(self.project_index_path, 'w') as output_file:
            json.dump(index, output_file, indent=4)
        self.close()

    def _walk(self, parent, index, level):
        labels = ['sequences', 'shots']

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


class MyTreeWidget(QtWidgets.QTreeWidget):
    def mousePressEvent(self, event):
        if not self.indexAt(event.pos()).isValid():
            self.selectionModel().clear()
        return super(MyTreeWidget, self).mousePressEvent(event)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = ProjectIndex()
    w.show()
    sys.exit(app.exec_())
