/*
    Manager suggestion by consulting with code action provider .
*/
import { TutorCodeActionProvider } from "./tutorCodeActionProvider";
import * as vscode from 'vscode';

export function initialize(context: vscode.ExtensionContext, mode: number){
    let tutor = new TutorCodeActionProvider();
    tutor.setMode(mode);

    vscode.languages.registerCodeActionsProvider(
        "python",
        tutor,
    );
	
	if (vscode.window.activeTextEditor) {
        tutor.update(vscode.window.activeTextEditor.document);
    }

    context.subscriptions.push(vscode.workspace.onDidChangeTextDocument(event => {
        if (event) {
            tutor.update(event.document);
        }
    }));
}