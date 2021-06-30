import * as vscode from 'vscode';
import { initialize as initializeModeManager } from './modeManager';
import { initialize as initializeSuggestionManager } from './suggestionManager';

export async function activate(context: vscode.ExtensionContext) {
    let mode = initializeModeManager(context);
    initializeSuggestionManager(context, mode);
}
