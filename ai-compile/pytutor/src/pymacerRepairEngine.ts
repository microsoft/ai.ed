/*
	PyMacer repair engine, implements the generic interface RepairEngine.
	This code is hacky because of no control over what pymacer returns.
*/

import * as vscode from 'vscode';
import * as https from 'https';
import axios from 'axios';
import { RepairEngine } from './repairEngine';
import { compiles, EXTENSION_NAME, getModeIcon } from './util';

const PYMACER_REQUEST_TIMEOUT = 10000;
const PYMACER_SERVER_URL = "http://127.0.0.1:5000/getfixes";
const PYTHON_PATH = "C://venv//pymacer//Scripts//python"

interface PyMacerEditSuggestion {
	type: string;           // type of edit operation - insert/ delete/ replace
	start: number;          // starting position of the edit to be made
	end: number;            // ending position of the edit to be made
	insertString: string;   // text to be inserted in the range defined above
}

interface PyMacerFeedback {
	fullText: string;       // complete Feedback Text: concatenation of msg1 + msg2 + actionMsg + tokensText + tokens
	msg1: string;           // generic message quoting existance of error
	msg2: string;           // specific message quoting kind of edits required to correct
	actionMsg: string;		// message specifying the action that should be taken
	tokensText: string[];   // textual description of the tokens that involve the action
	tokens: string[];       // actual tokens on which the action should be performed	
	action: string;			// type of the action suggested, one of insert/ delete/ replace
	misc: string;			// misc message	
}

interface PyMacerResponse {
	lineNo: number;							// the line that contains the error
	repairLine: string;     				// corrected version of the erroneous source line
	editDiffs: PyMacerEditSuggestion[];		// edit suggestions that will fix the incorrect source line
	feedback: PyMacerFeedback[];   			// feedback in natural language for learning purposes
	repairClasses: string[];				// short-hand name for the type of repair
}

export class PyMacerRepairEngine implements RepairEngine {
	context: vscode.ExtensionContext;
	responses: PyMacerResponse[] = [];
	diagnosticToCodeActionMap: Map<vscode.Diagnostic, vscode.CodeAction> = new Map();
	constructor(context: vscode.ExtensionContext){
		this.context = context;
	}
	async process(): Promise<boolean> {
		this.responses = [];
		this.diagnosticToCodeActionMap.clear();
		let didCompile = await compiles(PYTHON_PATH);
		if (didCompile === false) {
			console.log('Syntax Error... Consulting PyMacer')
			let data = {
				source: vscode.window.activeTextEditor?.document.getText(),
				lastEditLine: vscode.window.activeTextEditor?.selection.active.line
			};
			try {
				const pymacerResponse = await axios.post(
					PYMACER_SERVER_URL,
					JSON.parse(JSON.stringify(data)),
					{
						timeout: PYMACER_REQUEST_TIMEOUT,
						httpsAgent: new https.Agent({ rejectUnauthorized: false })
					}
				);
				this.responses = pymacerResponse.data.repairs as PyMacerResponse[];
			} catch (exception) {
				console.error(exception);
				return false;
			}
		}
		this.populateDiagnosticsAndCodeActions();
		return true;
	}

	populateDiagnosticsAndCodeActions(){
		for (let i = 0; i < this.responses.length; i++) {
			let response = this.responses[i];
			let code = vscode.window.activeTextEditor?.document.getText();
			if (code === undefined){
				code = "";
			}
			let range = undefined; 
			try {
				range = new vscode.Range(
						new vscode.Position(response.lineNo, response.editDiffs[0].start),
						new vscode.Position(response.lineNo, response.editDiffs[0].end + 1)
				)
			}
			catch(exception)
			{
				range = new vscode.Range(
					new vscode.Position(response.lineNo, 0),
					new vscode.Position(response.lineNo, code[response.lineNo].length)
				);
			}

			let diagnosticMessage = "";
			let actionMessage = "";
			try{
				diagnosticMessage = response.feedback[0].msg1 + response.feedback[0].msg2;
				actionMessage = response.feedback[0].fullText.split(response.feedback[0].msg2)[1].trim();				
			}
			catch{
				diagnosticMessage = "";
				actionMessage = "";
			}
			let diagnostic = {
				range: range,
				message: diagnosticMessage,
				severity: vscode.DiagnosticSeverity.Warning,
				source: EXTENSION_NAME + getModeIcon(this.context)				
			}
			let action = new vscode.CodeAction(
				actionMessage,
				vscode.CodeActionKind.QuickFix
			);
			this.diagnosticToCodeActionMap.set(diagnostic, action);
		}
	}
}