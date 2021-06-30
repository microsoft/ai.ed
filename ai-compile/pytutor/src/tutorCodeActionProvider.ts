/*
  Provider for code actions based on diagnostics
*/

import * as vscode from 'vscode';
import * as path from 'path';
import { EXTENSION_NAME, Modes } from './util';

export class TutorCodeActionProvider implements vscode.CodeActionProvider {

    private mode: Modes = 0;
    private codeActions: Map<vscode.Diagnostic, vscode.CodeAction> = new Map();
    public diagnosticCollection = vscode.languages.createDiagnosticCollection(
        "Python Tutor"
    );

    public setMode(mode: Modes) {
        this.mode = mode;
    }  
    
    public update(document: vscode.TextDocument) {
        if (document && path.basename(document.uri.fsPath) === "rainfall.py") {
            this.codeActions.clear();
            const diagnostics: vscode.Diagnostic[] = [];
        
            let line = document.lineAt(11).text;
            if (line.includes("else")) {
                const diagnostic = {
                    code: "",
                    message:
                    "😞 Python couldn't understand your program.\n\n" +
                    "Try changing 'else' to something different. Recall the differences between 'if', 'elif', and 'else'.",
                    range: new vscode.Range(
                    new vscode.Position(11, 4),
                    new vscode.Position(11, 8)
                    ),
                    severity: vscode.DiagnosticSeverity.Warning,
                    source: EXTENSION_NAME,
                };

                let action = new vscode.CodeAction(
                    "Learn more about control flow statements",
                    vscode.CodeActionKind.Empty
                );

                action.command = {
                    command: "vscode.open",
                    title: "",
                    arguments: [
                    vscode.Uri.parse(
                        "https://docs.python.org/3/tutorial/controlflow.html"
                    ),
                    ],
                };
                action.diagnostics = [diagnostic];

                this.codeActions.set(diagnostic, action);
                diagnostics.push(diagnostic);
            }
            this.diagnosticCollection.set(document.uri, diagnostics);
        }
    }

    public provideCodeActions(
        document: vscode.TextDocument,
        range: vscode.Range | vscode.Selection,
        context: vscode.CodeActionContext,
        token: vscode.CancellationToken
      ): vscode.CodeAction[] {
        let codeActions = [];
        for (let diagnostic of context.diagnostics) {
          let codeAction = this.codeActions.get(diagnostic);
          if (codeAction) {
            codeActions.push(codeAction);
          }
        }    
        return codeActions;
      }
}