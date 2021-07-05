/*
  Provider for code actions based on diagnostics
*/

import * as vscode from 'vscode';
import { PyMacer as PyMacerRepairEngine } from './pymacer';
import { RepairEngine, RepairEngineTypes } from './repairEngine';
import { Modes } from './util';

export class TutorCodeActionProvider implements vscode.CodeActionProvider {
	private mode: Modes;
	private repairEngine: RepairEngine;
	private mapDiagnosticToCodeActions: Map<vscode.Diagnostic, vscode.CodeAction> = new Map();

	public constructor(mode: Modes, repairEngineType: RepairEngineTypes) {
		this.mode = mode;
		if (repairEngineType === RepairEngineTypes.PyMacer){
			this.repairEngine = new PyMacerRepairEngine();			
		}
		else{
			this.repairEngine = undefined!;
		}
	}

	public async update() {
		this.mapDiagnosticToCodeActions.clear();
		let status = await this.repairEngine.process(this.mode);
		if (!status){
			console.error('Consultation with repair engine failed.')
		}
		else{
			this.mapDiagnosticToCodeActions = this.repairEngine.populateCodeActions();
		}
	}

	public provideCodeActions(
		document: vscode.TextDocument,
		range: vscode.Range | vscode.Selection,
		context: vscode.CodeActionContext,
		token: vscode.CancellationToken
	): vscode.CodeAction[] {
		let codeActions: vscode.CodeAction[] = [];
		for (let diagnostic of context.diagnostics) {
			let codeAction = this.mapDiagnosticToCodeActions.get(diagnostic);
			if (codeAction) {
				codeActions.push(codeAction);
			}
		}
		return codeActions;
	}
}