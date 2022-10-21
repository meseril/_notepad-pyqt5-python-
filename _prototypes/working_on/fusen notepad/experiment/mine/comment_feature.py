
"""
Created by Matic Kukovec
"""
# QtCore.Qt.Key documentation : https://doc.qt.io/qtforpython-5/PySide2/QtCore/Qt.html

# Import the PyQt5 module with some of the GUI widgets
import PyQt5.QtWidgets
import PyQt5.QtGui
import PyQt5.QtCore
# Import the QScintilla module
import PyQt5.Qsci
# Import Python's sys module needed to get the application arguments
import sys

"""
Custom editor with a simple commenting feature
similar to what SublimeText does
"""
class MyCommentingEditor(PyQt5.Qsci.QsciScintilla):
    comment_string = "# "
    line_ending = "\n"
    
    def keyPressEvent(self, event):
        # Execute the superclasses event
        super().keyPressEvent(event)
        # Check pressed key information
        key = event.key()
        key_modifiers = PyQt5.QtWidgets.QApplication.keyboardModifiers()
        if (key == PyQt5.QtCore.Qt.Key_K and 
            key_modifiers == PyQt5.QtCore.Qt.ControlModifier):
                self.toggle_commenting()
    
    def toggle_commenting(self):
        # Check if the selections are valid
        selections = self.get_selections()
        if selections == None:
            return
        # Merge overlapping selections
        while self.merge_test(selections) == True:
            selections = self.merge_selections(selections)
        # Start the undo action that can undo all commenting at once
        self.beginUndoAction()
        # Loop over selections and comment them
        for i, sel in enumerate(selections):
            if self.text(sel[0]).lstrip().startswith(self.comment_string):
                self.set_commenting(sel[0], sel[1], self._uncomment)
            else:
                self.set_commenting(sel[0], sel[1], self._comment)
        # Select back the previously selected regions
        self.SendScintilla(self.SCI_CLEARSELECTIONS)
        for i, sel in enumerate(selections):
            start_index = self.positionFromLineIndex(sel[0], 0)
            # Check if ending line is the last line in the editor
            last_line = sel[1]
            if last_line == self.lines() - 1:
                end_index = self.positionFromLineIndex(sel[1], len(self.text(last_line)))
            else:
                end_index = self.positionFromLineIndex(sel[1], len(self.text(last_line))-1)
            if i == 0:
                self.SendScintilla(self.SCI_SETSELECTION, start_index, end_index)
            else:
                self.SendScintilla(self.SCI_ADDSELECTION, start_index, end_index)
        # Set the end of the undo action
        self.endUndoAction()
    
    def get_selections(self):
        # Get the selection and store them in a list
        selections = []
        for i in range(self.SendScintilla(self.SCI_GETSELECTIONS)):
            selection = (
                self.SendScintilla(self.SCI_GETSELECTIONNSTART, i),
                self.SendScintilla(self.SCI_GETSELECTIONNEND, i)
            )
            # Add selection to list
            from_line, from_index = self.lineIndexFromPosition(selection[0])
            to_line, to_index = self.lineIndexFromPosition(selection[1])
            selections.append((from_line, to_line))
        selections.sort()
        # Return selection list
        return selections
    
    def merge_test(self, selections):
        """
        Test if merging of selections is needed
        """
        for i in range(1, len(selections)):
            # Get the line numbers
            previous_start_line = selections[i-1][0]
            previous_end_line = selections[i-1][1]
            current_start_line = selections[i][0]
            current_end_line = selections[i][1]
            if previous_end_line == current_start_line:
                return True
        # Merging is not needed
        return False
    
    def merge_selections(self, selections):
        """
        This function merges selections with overlapping lines
        """
        # Test if merging is required
        if len(selections) < 2:
            return selections
        merged_selections = []
        skip_flag = False
        for i in range(1, len(selections)):
            # Get the line numbers
            previous_start_line = selections[i-1][0]
            previous_end_line = selections[i-1][1]
            current_start_line = selections[i][0]
            current_end_line = selections[i][1]
            # Test for merge
            if previous_end_line == current_start_line and skip_flag == False:
                merged_selections.append(
                    (previous_start_line, current_end_line)
                )
                skip_flag = True
            else:
                if skip_flag == False:
                    merged_selections.append(
                        (previous_start_line, previous_end_line)
                    )
                skip_flag = False
                # Add the last selection only if it was not merged
                if i == (len(selections) - 1):
                    merged_selections.append(
                        (current_start_line, current_end_line)
                    )
        # Return the merged selections
        return merged_selections
    
    def set_commenting(self, arg_from_line, arg_to_line, func):
        # Get the cursor information
        from_line = arg_from_line
        to_line = arg_to_line
        # Check if ending line is the last line in the editor
        last_line = to_line
        if last_line == self.lines() - 1:
            to_index = len(self.text(to_line))
        else:
            to_index = len(self.text(to_line))-1
        # Set the selection from the beginning of the cursor line
        # to the end of the last selection line
        self.setSelection(
            from_line, 0, to_line, to_index
        )
        # Get the selected text and split it into lines
        selected_text = self.selectedText()
        selected_list = selected_text.split("\n")
        # Find the smallest indent level
        indent_levels = []
        for line in selected_list:
            indent_levels.append(len(line) - len(line.lstrip()))
        min_indent_level = min(indent_levels)
        # Add the commenting character to every line
        for i, line in enumerate(selected_list):
            selected_list[i] = func(line, min_indent_level)
        # Replace the whole selected text with the merged lines
        # containing the commenting characters
        replace_text = self.line_ending.join(selected_list)
        self.replaceSelectedText(replace_text)
    
    def _comment(self, line, indent_level):
        if line.strip() != "":
            return line[:indent_level] + self.comment_string + line[indent_level:]
        else:
            return line
    
    def _uncomment(self, line, indent_level):
        if line.strip().startswith(self.comment_string):
            return line.replace(self.comment_string, "", 1)
        else:
            return line

        

# Create the main PyQt application object
application = PyQt5.QtWidgets.QApplication(sys.argv)

# Create a QScintila editor instance
editor = MyCommentingEditor()
editor.setMarginType(1, PyQt5.Qsci.QsciScintilla.NumberMargin)
editor.SendScintilla(editor.SCI_SETMULTIPLESELECTION, 1)
editor.SendScintilla(editor.SCI_SETADDITIONALSELECTIONTYPING, True)

# Show the editor
editor.show()
editor.resize(PyQt5.QtCore.QSize(800, 600))
# Put the text into the editing area of the editor
editor.setText(
"""\
#include <iostream>
using namespace std;
void Function0() {
    cout << "Function0";
}
void Function1() {
    cout << "Function1";
}
void Function2() {
    cout << "Function2";
}
void Function3() {
    cout << "Function3";
}
int main(void) {
    if (1) {
        if (1) {
            if (1) {
                if (1) {
                    int yay;
                }
            }
        }
    }
    if (1) {
        if (1) {
            if (1) {
                if (1) {
                    int yay2;
                }
            }
        }
    }
    return 0;
}\
"""
)

# Execute the application
application.exec_()