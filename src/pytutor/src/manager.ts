/*
	Manages global properties such as mode of operation (currently two modes are supported: beginner and expert)
*/

import * as vscode from 'vscode';
import { Modes, MODE_MEMENTO_NAME, getModeIcon } from './util';

export class Manager {
	static context: vscode.ExtensionContext;
	constructor(context: vscode.ExtensionContext) {
		Manager.context = context;
		let mode = Manager.context.globalState.get(MODE_MEMENTO_NAME, Modes.Beginner);
		vscode.commands.executeCommand('setContext', 'pythontutor.mode', mode);

		Manager.context.subscriptions.push(vscode.commands.registerCommand("python-tutor.beginner-mode", handleBeginnerMode));
		Manager.context.subscriptions.push(vscode.commands.registerCommand("python-tutor.expert-mode", handleExpertMode));

		if (mode === Modes.Beginner) {
			handleBeginnerMode();
		}
		else {
			handleExpertMode();
		}
	}
}

export async function handleBeginnerMode() {
	Manager.context.globalState.update(MODE_MEMENTO_NAME, Modes.Beginner);
	vscode.commands.executeCommand('setContext', 'pythontutor.beginner', true);
	vscode.commands.executeCommand('setContext', 'pythontutor.expert', false);
	vscode.window.showInformationMessage('Python Tutor: Beginner Mode Activated ' + getModeIcon(Manager.context));
}

export async function handleExpertMode() {
	Manager.context.globalState.update(MODE_MEMENTO_NAME, Modes.Expert);
	vscode.commands.executeCommand('setContext', 'pythontutor.beginner', false);
	vscode.commands.executeCommand('setContext', 'pythontutor.expert', true);
	vscode.window.showInformationMessage('Python Tutor: Expert Mode Activated ' + getModeIcon(Manager.context));
}