import * as vscode from 'vscode';
import { Manager } from './manager';
import { RepairEngineTypes } from './repairEngine';
import { TutorCodeActionProvider } from './tutorCodeActionProvider';

export async function activate(context: vscode.ExtensionContext) {
    new Manager(context);

    let tutorAction = new TutorCodeActionProvider(context, RepairEngineTypes.PyMacer);
    vscode.languages.registerCodeActionsProvider(
        "python",
        tutorAction,
    );

}
