import canvas
import argparse
import re
import sys

class BetterErrorParser(argparse.ArgumentParser):
    def error(self, message, help=True):
        sys.stderr.write('error: %s\n' % message)
        if help:
            self.print_help()
        sys.exit(2)


class ObjectType:
    def __init__(self, type_name, text_fields, title_field=None):
        self.type_name = type_name
        self.text_fields = text_fields if isinstance(text_fields, list) else [text_fields]
        self.title_field = title_field

    def process_one(self, obj, compiled_regex, repl):
        print()
        print("---------------------------------------------------------------")
        if self.title_field:
            print("Processing object: %s" % obj[self.title_field])
        else:
            print("Processing next object")
        
        for text_field in self.text_fields:
            update_needed = False

            print("Processing text field: %s" % text_field)
            old_value = obj[text_field]
            (new_value, count) = compiled_regex.subn(repl, old_value, count=0)
            if count > 0:
                update_needed = True
                obj[text_field] = new_value
                print("Replaced %s matches" % count)
                print("Old value:")
                print(old_value)
                print()
                print()
                print("New value:")
                print(new_value)
                print()
                print()
            else:
                print("No replacements made.")
        
        if update_needed:
            print("Making update on Canvas...")
            obj.update()
            print("Update complete.")

        if self.title_field:
            print("Done processing object: %s" % obj[self.title_field])
        else:
            print("Done processing object")

    def process(self, objects, compiled_regex, repl):
        print("Processing %s objects" % self.type_name)
        print("Title field is %s" % (self.title_field if self.title_field else "not present"))
        print("Text fields: %s" % (", ".join(self.text_fields)))

        for obj in objects:
            self.process_one(obj, compiled_regex, repl)

parser = BetterErrorParser()
canvas.Canvas.add_arguments(parser)

# TODO: help users with creating regular expressions (e.g., have a mode that displays the regexes and takes a test string to act on but doesn't act on Canvas?)
# TODO: modify Canvas so that the file is optional and it will look for a default like token.txt (which should be in .gitignore!) if no argument is given and only then complain
# TODO: make optionally interactive with confirmation of changes (via diffing?)
# TODO: reasonable logging
# TODO: need I avoid passing the extra args along to canvas.Canvas?


parser.add_argument("-a", "--assignments", help="Process assignments.", action="store_true")
parser.add_argument("-p", "--pages", help="Process pages.", action="store_true")
parser.add_argument("-q", "--quizzes", help="Process quizzes.", action="store_true")
parser.add_argument("-A", "--all", help="Process all types (assignments, pages, and quizzes).", action="store_true")
parser.add_argument("regex", help="The regular expression (using Python's re syntax) to search for.")
parser.add_argument("repl", help="The replacement string (using Python's syntax from re.sub) with which to replace regex.")
args = parser.parse_args()

process_assns = args.assignments or args.all
process_quizzes = args.quizzes or args.all
process_pages = args.pages or args.all
if not (process_assns or process_pages or process_quizzes):
    parser.error("You must use a flag to indicate processing of at least one type.")

assn_type = ObjectType("assignment", "description", "name")
page_type = ObjectType("page", "body", "url")
quiz_type = ObjectType("quiz", "description", "title")

compiled_regex = re.compile(args.regex)
repl = args.repl

canvas = canvas.Canvas(args=args)

print('Object types being processed: %s%s%s' % \
    ("assignments " if process_assns else "",
    "pages " if process_pages else "",
    "quizzes " if process_quizzes else ""))


print('Reading data from Canvas...')
course = canvas.course(args.course, prompt_if_needed=True)
print('Using course: %s / %s' % (course['term']['name'],
                                 course['course_code']))


if process_assns:
    print("Fetching assignments from Canvas...")
    assignments = course.assignments()
    print("Done fetching assignments from Canvas.")
    assn_type.process(assignments, compiled_regex, repl)

if process_pages:
    print("Fetching pages from Canvas...")
    pages = course.pages()
    print("Done fetching pages from Canvas.")
    page_type.process(pages, compiled_regex, repl)

if process_quizzes:
    print("Fetching quizzes from Canvas...")
    quizzes = course.quizzes()
    print("Done fetching quizzes from Canvas.")
    quiz_type.process(quizzes, compiled_regex, repl)



# Note: for some reason, Course.assignments filters out "online_quiz" assignment types. Should it?? Are those "Quiz" instead?
