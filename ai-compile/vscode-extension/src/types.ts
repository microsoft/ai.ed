export interface Payload {
  source: string;
  lastEditLine: number;
}



export interface Edit {
  type: string;
  start: number;
  end: number;
  insertString: string;
}

export interface Feedback {
  fullText: string;
  msg1: string;
  msg2: string;
  misc: string;
  actionMsg: string;
  action: string;
  tokens: string[];
  tokensText: string[];

}

export interface Response {
  lineNo: number;
  repairLine: string;
  editDiffs: Edit[];
  feedback: Feedback[];
  repairClasses: string[];
}

export interface DocumentStore {
  // TODO: Can this be made private? Does it make sense?
  filePath: string;
  fixes: Fix;
}

export type Fix = Response[] | undefined;
