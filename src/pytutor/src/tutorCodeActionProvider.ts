/*
	Provider for code actions based on diagnostics
*/

import * as vscode from 'vscode';
import { RepairEngineTypes } from './repairEngine';
import { getModeIcon } from './util';

export class TutorCodeActionProvider implements vscode.CodeActionProvider {
	public diagnosticCollection = vscode.languages.createDiagnosticCollection(
		"PythonTutor"
	);
	public codeActions: vscode.CodeAction[] = [];
	public context: vscode.ExtensionContext;
	
	public constructor(context: vscode.ExtensionContext, repairEngineType: RepairEngineTypes) {
		this.context = context;		
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

		context.subscriptions.push(vscode.workspace.onDidOpenTextDocument(event => {
			if (event) {
				if (vscode.window.activeTextEditor) {
					this.update(vscode.window.activeTextEditor.document);
				}
			}
		}));
		
		context.subscriptions.push(vscode.workspace.onDidChangeTextDocument(event => {
			if (event) {
				if (vscode.window.activeTextEditor) {
					this.update(vscode.window.activeTextEditor.document);
				}
			}
		}));
	}

	public async update(document: vscode.TextDocument) {
		let diagnostics = [];
		this.codeActions = [];
		if (document.fileName.includes("division.py")){	
			let error = "x/y=a";
			let errorLine = 3;
			let correction = "a = x/y";
			let line = document.lineAt(errorLine).text;
			if (line.includes(error)) {
				let start = line.indexOf(error);
				let end = start + error.length;

				const diagnostic = {
					code: "",
					message:
					"Look closely on both sides of '='.\n"+
					"When you write x = y, value of y is copied to x, not the other way around!\n\n"+
					"👉 Rule to remember: '=' is an assignment operator to assigns right side to left side",
					range: new vscode.Range(
						new vscode.Position(errorLine, start),
						new vscode.Position(errorLine, end)
					),
					severity: vscode.DiagnosticSeverity.Warning,
					source: "PyTutor " + getModeIcon(this.context),
				};

				const action = new vscode.CodeAction(
					"Swap operands on both sides of the '=' operator",
					vscode.CodeActionKind.QuickFix
				);

				action.edit = new vscode.WorkspaceEdit();
				action.edit.replace(
					document.uri,
					new vscode.Range(
						new vscode.Position(errorLine, start),
						new vscode.Position(errorLine, end)
					),
					correction
				);
				action.diagnostics = [diagnostic];
				this.codeActions.push(action);
				diagnostics.push(diagnostic);
			}
		}

		if (document.fileName.includes("multiplication.py")){
			let error = "3s";
			let errorLine = 5;
			
			let line = document.lineAt(errorLine).text;
			if (line.includes(error)) {
				let start = line.indexOf(error);
				let end = start + error.length;

				const diagnostic = {
					code: "",
					message:
					"Looks like you missed a binary operator here.\n"+
					"'5x' does NOT mean 5 multipled by x, write '5 * x' instead!\n\n"+
					"👉 Rule to remember: The multiplication operator '*' multiplies two operands.",
					range: new vscode.Range(
						new vscode.Position(errorLine, start),
						new vscode.Position(errorLine, end)
					),
					severity: vscode.DiagnosticSeverity.Warning,
					source: "PyTutor " + getModeIcon(this.context),
				};

				const action1 = new vscode.CodeAction(
					"Replace with 3 * s",
					vscode.CodeActionKind.QuickFix
				);
				const action2 = new vscode.CodeAction(
					"Replace with 3 + s",
					vscode.CodeActionKind.QuickFix
				);
				const action3 = new vscode.CodeAction(
					"Replace with s3",
					vscode.CodeActionKind.QuickFix
				);

				action1.edit = new vscode.WorkspaceEdit();
				action1.edit.replace(
					document.uri,
					new vscode.Range(
						new vscode.Position(errorLine, start),
						new vscode.Position(errorLine, end)
					),
					"3 * s"
				);

				action2.edit = new vscode.WorkspaceEdit();
				action2.edit.replace(
					document.uri,
					new vscode.Range(					
						new vscode.Position(errorLine, start),
						new vscode.Position(errorLine, end)
					),
					"3 + s"
				);

				action3.edit = new vscode.WorkspaceEdit();
				action3.edit.replace(
					document.uri,
					new vscode.Range(
						new vscode.Position(errorLine, start),
						new vscode.Position(errorLine, end)
					),
					"s3"
				);

				action1.diagnostics = [diagnostic];
				action2.diagnostics = [diagnostic];
				action3.diagnostics = [diagnostic];
				
				this.codeActions.push(action1);
				this.codeActions.push(action2);
				this.codeActions.push(action3);

				diagnostics.push(diagnostic);
			}
		}

		this.diagnosticCollection.set(document.uri, diagnostics);
	}

	public provideCodeActions(
		document: vscode.TextDocument,
		range: vscode.Range | vscode.Selection,
		context: vscode.CodeActionContext,
		token: vscode.CancellationToken
	): vscode.CodeAction[] {		
		return this.codeActions;  
	}
}