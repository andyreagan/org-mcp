#!/usr/bin/env python3
"""
Script to generate README.md from README.org
Adds GitHub Actions badges
"""
import os
import re


def convert_org_to_md(org_content):
    """Convert org-mode syntax to markdown"""
    md_content = []

    # We'll handle titles and badges in the conversion process

    # Process each line
    for line in org_content.splitlines():
        # Skip CREATED and UPDATED lines
        if line.startswith("#+CREATED:") or line.startswith("#+UPDATED:"):
            continue

        # Handle HTML tags (especially for badges)
        if line.startswith("#+HTML:"):
            md_content.append(line.replace("#+HTML:", "").strip())
            continue

        # Convert org link syntax to markdown
        if "[[" in line and "]]" in line:
            # Convert org links to markdown links
            line = re.sub(r"\[\[(.*?)\]\[(.*?)\]\]", r"[\2](\1)", line)

        # Convert headers - first level header will be # not ##
        if line.startswith("* "):
            md_content.append("# " + line[2:])
        elif line.startswith("** "):
            md_content.append("## " + line[3:])
        elif line.startswith("*** "):
            md_content.append("### " + line[4:])
        # Convert src blocks
        elif line.startswith("#+begin_src"):
            lang = line.replace("#+begin_src", "").strip()
            md_content.append("```" + lang)
        elif line.startswith("#+end_src"):
            md_content.append("```")
        # Convert bullet points
        elif line.startswith("- "):
            md_content.append(line)
        # Pass through other content
        else:
            md_content.append(line)

    return "\n".join(md_content)


def main():
    # Get the project root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    # Read README.org
    org_path = os.path.join(project_root, "README.org")
    with open(org_path, encoding="utf-8") as f:
        org_content = f.read()

    # Convert to markdown
    md_content = convert_org_to_md(org_content)

    # Write README.md
    md_path = os.path.join(project_root, "README.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"Generated {md_path} from {org_path}")


if __name__ == "__main__":
    main()
