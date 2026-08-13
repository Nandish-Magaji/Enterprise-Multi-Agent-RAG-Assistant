"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import rehypeRaw from "rehype-raw";

import "highlight.js/styles/github-dark.css";

interface Props{
    content: string;
}

export default function DocumentRenderer({
    content
}:Props){
    const cleanedContent = content
        .replace(/^```markdown/i, "")
        .replace(/^```md/i, "")
        .replace(/^```/i, "")
        .replace(/```$/i, "")
        .trim();

    if (!cleanedContent) {
    return (
        <p className="text-zinc-500 italic">
            No content generated yet.
        </p>
    );
    }    

    return(
        <article
            className="
                markdown-body
                prose
                prose-zinc
                dark:prose-invert
                max-w-none
        ">

            <ReactMarkdown
                skipHtml={false}
                remarkPlugins={[
                    remarkGfm,
                ]}
                rehypePlugins={[
                    rehypeRaw,
                    rehypeHighlight,
                ]}
            >
                {cleanedContent}
            </ReactMarkdown>

        </article>

    )

}