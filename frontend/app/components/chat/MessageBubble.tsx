"use client";

import WorkflowDocument from "../workflow/WorkflowDocument";
import { Message } from "@/types/chat";

interface Props{
    message:Message;
}

export default function MessageBubble({
    message,
}:Props){

    const isUser=message.role==="user";
    const isSystem=message.role==="system";

    if(isSystem){

        return(

            <div className="mx-auto max-w-2xl rounded-lg border bg-white px-4 py-3 text-center text-sm">

                {message.content}

            </div>

        );

    }

    return(

        <div className={`flex ${isUser?"justify-end":"justify-start"}`}>

            <div
                className={`max-w-[92%] rounded-xl p-4 ${
                    isUser
                    ? "bg-zinc-900 text-white"
                    : "border bg-white"
                }`}
            >

                {message.workflow
                    ?(
                        <WorkflowDocument
                            workflow={message.workflow}
                        />
                    )
                    :(
                        <div className="whitespace-pre-wrap">

                            {message.content}

                        </div>
                    )
                }

            </div>

        </div>

    );

}