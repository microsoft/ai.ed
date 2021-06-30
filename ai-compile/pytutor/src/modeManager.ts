/*
    Manages mode of operation (currently two modes are supported: beginner and expert)
*/

import * as vscode from 'vscode';
import { Modes, MODE_MEMENTO_NAME, getModeIcon } from './util';

let globalState: vscode.Memento;

export function initialize(context: vscode.ExtensionContext){
    globalState = context.globalState;
    let mode = globalState.get(MODE_MEMENTO_NAME, Modes.Beginner);
    vscode.commands.executeCommand('setContext', 'pythontutor.mode', mode);

    context.subscriptions.push(vscode.commands.registerCommand("python-tutor.beginner-mode", handleBeginnerMode));
    context.subscriptions.push(vscode.commands.registerCommand("python-tutor.expert-mode", handleExpertMode));

    if (mode === Modes.Beginner){
      handleBeginnerMode();
    }
    else{
      handleExpertMode();
    }
    return mode;
}

export async function handleBeginnerMode() {
    globalState.update(MODE_MEMENTO_NAME, Modes.Beginner);
    vscode.commands.executeCommand('setContext', 'pythontutor.beginner', true);
    vscode.commands.executeCommand('setContext', 'pythontutor.expert', false);
    vscode.window.showInformationMessage('Python Tutor: Beginner Mode Activated ' + getModeIcon(Modes.Beginner));
}

export async function handleExpertMode() {
  globalState.update(MODE_MEMENTO_NAME, Modes.Expert);
  vscode.commands.executeCommand('setContext', 'pythontutor.beginner', false);
  vscode.commands.executeCommand('setContext', 'pythontutor.expert', true);
  vscode.window.showInformationMessage('Python Tutor: Expert Mode Activated ' +  getModeIcon(Modes.Expert));
}