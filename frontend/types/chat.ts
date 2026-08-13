import { WorkflowResult } from "./workflow";

export interface Message {

    id:string;

    role:"user"|"assistant"|"system";

    content:string;

    workflow?:WorkflowResult;

}