export interface Payload {
  source: string;
  lastEditLine: number;
}

export interface Feedback {
  fullText: string;
  msg1: string;
  msg2: string;
  misc: string;
  actionMsg: string;
  actoin: string;
  tokens: string[];
  tokensText: string[];
}

export interface Response {
  lineNo: number;
  repairLine: string;
  feedback: Feedback[];
  repairClasses: string[];
}

export interface DocumentStore {
  // TODO: Can this be made private? Does it make sense?
  filePath: string;
  fixes: Fix;
}

export type Fix = Response[] | undefined;
