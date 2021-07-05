/*
	Provider for code actions based on diagnostics
*/

import * as vscode from 'vscode';
import { PyMacerRepairEngine as PyMacerRepairEngine } from './pymacerRepairEngine';
import { RepairEngine, RepairEngineTypes } from './repairEngine';

export class TutorCodeActionProvider implements vscode.CodeActionProvider {
	private repairEngine: RepairEngine;
	public diagnosticCollection = vscode.languages.createDiagnosticCollection(
		"PythonTutor"
	);

	public constructor(context: vscode.ExtensionContext, repairEngineType: RepairEngineTypes) {			
		if (repairEngineType === RepairEngineTypes.PyMacer){
			this.repairEngine = new PyMacerRepairEngine(context);			
		}
		else{
			this.repairEngine = undefined!;
		}		
		if (vscode.window.activeTextEditor) {
			this.update(vscode.window.activeTextEditor.document);
		}
		context.subscriptions.push(vscode.workspace.onDidSaveTextDocument(event => {
			if (event) {
				if (vscode.window.activeTextEditor) {
					this.update(vscode.window.activeTextEditor.document);
				}
			}
		}));
	}

	public async update(document: vscode.TextDocument) {
		let status = await this.repairEngine.process();
		if (!status){
			console.error('Consultation with repair engine failed.')
		}
		let diagnostics = [];
		for(let diagnostic of this.repairEngine.diagnosticToCodeActionMap.keys()){
			diagnostics.push(diagnostic);
		}
		this.diagnosticCollection.set(document.uri, diagnostics);
		
	}

	public provideCodeActions(
		document: vscode.TextDocument,
		range: vscode.Range | vscode.Selection,
		context: vscode.CodeActionContext,
		token: vscode.CancellationToken
	): vscode.CodeAction[] {
		let codeActions: vscode.CodeAction[] = [];
		for (let diagnostic of context.diagnostics) {
			let codeAction = this.repairEngine.diagnosticToCodeActionMap.get(diagnostic);
			if (codeAction) {
				codeActions.push(codeAction);
			}
		}
		return codeActions;
	}
}