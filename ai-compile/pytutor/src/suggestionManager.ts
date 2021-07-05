/*
    Manages suggestion by consulting with code action provider .
*/

import * as vscode from 'vscode';
import { RepairEngineTypes } from './repairEngine';
import { TutorCodeActionProvider } from "./tutorCodeActionProvider";
import { Modes } from "./util";

export function initialize(context: vscode.ExtensionContext, mode: Modes){
    let tutorAction = new TutorCodeActionProvider(mode, RepairEngineTypes.PyMacer);

    vscode.languages.registerCodeActionsProvider(
        "python",
        tutorAction,
    );
	
    if (vscode.window.activeTextEditor) {
        tutorAction.update();
    }

    context.subscriptions.push(vscode.workspace.onDidChangeTextDocument(event => {
        if (event) {
            tutorAction.update();
        }
    }));
}
