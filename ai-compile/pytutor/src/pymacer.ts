/*
	PyMacer repair engine, implements the generic interface RepairEngine.
*/

import * as vscode from 'vscode';
import * as https from 'https';
import axios from 'axios';
import { RepairEngine } from './repairEngine';
import { compiles, Modes } from './util';

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

export class PyMacer implements RepairEngine {
	mode: Modes = Modes.Beginner;
	responses:  PyMacerResponse[] = [];
	async process(mode: Modes): Promise<boolean>{
		this.mode = mode;
		this.responses = [];				
		let didCompile = await compiles(PYTHON_PATH);
		if (didCompile === false){
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
						httpsAgent: new https.Agent({rejectUnauthorized: false})
					}
				);
				this.responses = pymacerResponse.data.repairs as PyMacerResponse[];
			} catch (exception) {
				console.error(exception);
				return false;
			}
		}
		return true;	
	}
	populateCodeActions(): Map<vscode.Diagnostic, vscode.CodeAction> {
		for(let i = 0; i < this.responses.length; i++){
			let response = this.responses[i];
			// TODO: Map diagnostic --> action
	
		}
		return new Map();
	}	
}