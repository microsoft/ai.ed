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
	public codeActions: Map<String, vscode.CodeAction[]> = new Map();
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
		this.codeActions = new Map();
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
					"Look closely on both sides of '='\n"+
					"When you write x = y, value of y is copied to x (x <--y ), not the other way around!\n\n"+
					"👉 '=' is an assignment operator to assign right side to left side\n",
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
				let codeActionHash = document.uri.path + errorLine.toString();
				this.codeActions.set(codeActionHash, [action]);
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
					"Looks like you missed a binary operator here\n"+
					"'5x' does NOT mean 5 multipled by x, write '5 * x' instead!\n\n"+
					"👉 The multiplication operator '*' multiplies two operands\n",
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
				

				let codeActionHash = document.uri.path + errorLine.toString();
				this.codeActions.set(codeActionHash, [action1, action2, action3]);
				diagnostics.push(diagnostic);
			}
		}

		if (document.fileName.includes("odd-even.py")){	
			let errors = ["x%!=0", 'else'];
			let errorLines = [1, 4];
			let corrections = ['x % <<INSERT AN INTEGER HERE>> != 0', 'elif'];
			let messages = [
				"Look closely after the operator '%'\n"+
				"Did you miss putting a number here?\n\n"+				
				"👉 '%' is a binary operator and needs two operands on either sides\n",

				"Look closely on the keyword 'else'\n"+
				"Did you mean 'elif'?\n\n"+
				"👉 A condition follows keywords 'if' and 'elif', but not 'else'\n"
			]
			let actionMessages = [
				"Insert a placeholder for a missing number",
				"Replace else with elif"
			]

			for (let i of [0, 1]){
				let error = errors[i];
				let errorLine = errorLines[i];
				let correction = corrections[i];
				let message = messages[i];
				let actionMessage = actionMessages[i];

				let line = document.lineAt(errorLine).text;
				if (line.includes(error)) {
					let start = line.indexOf(error);
					let end = start + error.length;

					const diagnostic = {
						code: "",
						message: message,						
						range: new vscode.Range(
							new vscode.Position(errorLine, start),
							new vscode.Position(errorLine, end)
						),
						severity: vscode.DiagnosticSeverity.Warning,
						source: "PyTutor " + getModeIcon(this.context),
					};

					const action = new vscode.CodeAction(
						actionMessage,
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
					let codeActionHash = document.uri.path + errorLine.toString();
					this.codeActions.set(codeActionHash, [action]);
					diagnostics.push(diagnostic);
				}
			}
		}

		if (document.fileName.includes("sum.py")){	
			let error = "sum+ = x";
			let errorLine = 4;
			let correction = "sum += x";
			let message = 
				"Look closely on the operator '+ =', there should be no space in between\n"+
				"You did it correctly on Line 4\n\n"+
				"👉 '+=' operator adds two values together and assigns the final value to a variable\n"+
				"👉 x += y is equivalent to writing the following two lines:\n"+
				"\t z = x + y\n"+
				"\t x = z\n";
			let actionMessage = "Replace '+ =' with '+='";

			let line = document.lineAt(errorLine).text;
			if (line.includes(error)) {
				let start = line.indexOf(error);
				let end = start + error.length;
				const diagnostic = {
					code: "",
					message: message,					
					range: new vscode.Range(
						new vscode.Position(errorLine, start),
						new vscode.Position(errorLine, end)
					),
					severity: vscode.DiagnosticSeverity.Warning,
					source: "PyTutor " + getModeIcon(this.context),
				};

				const action = new vscode.CodeAction(
					actionMessage,
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
				let codeActionHash = document.uri.path + errorLine.toString();
				this.codeActions.set(codeActionHash, [action]);
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
	): vscode.CodeAction[] | undefined {
		try{			
			let codeActionHash = document.uri.path + range.start['line'].toString();
			return this.codeActions.get(codeActionHash);  
		}
		catch{
			return [];
		}
	}
}