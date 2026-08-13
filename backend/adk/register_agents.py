from agents.researcher import researcher
from agents.writer import writer
from agents.fact_checker import fact_checker
from agents.editor import editor


REGISTERED_AGENTS = {
    researcher.name: researcher,
    writer.name: writer,
    fact_checker.name: fact_checker,
    editor.name: editor,
}