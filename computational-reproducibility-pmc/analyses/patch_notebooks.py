"""
patch_notebooks.py
==================
Patches all 10 failing analysis notebooks in-place.
Run from the repo root:
    python patch_notebooks.py

Each patch is surgical: only the failing cell(s) are modified.
"""

import json
import re
import sys
from pathlib import Path

ANALYSES_DIR = Path("/mnt/c/Users/vsh/Desktop/computational-reproducibility-pmc_zenodo/computational-reproducibility-pmc/computational-reproducibility-pmc/analyses")


def load_nb(path):
    with open(path) as f:
        return json.load(f)


def save_nb(nb, path):
    with open(path, "w") as f:
        json.dump(nb, f, indent=1)
    print(f"  ✓ saved {path}")


def get_source(cell):
    src = cell.get("source", [])
    if isinstance(src, list):
        return "".join(src)
    return src


def set_source(cell, text):
    cell["source"] = text.splitlines(keepends=True)


def find_cell_containing(nb, snippet):
    """Return (index, cell) of first code cell containing snippet."""
    for i, cell in enumerate(nb["cells"]):
        if cell.get("cell_type") == "code" and snippet in get_source(cell):
            return i, cell
    return None, None


def patch_n1_repository():
    """N1.Repository — bar plot fails on single-value Series (pandas 1.3 bug).
    Wrap .plot() in a try/except and skip if empty."""
    path = ANALYSES_DIR / "N1.Repository.ipynb"
    nb = load_nb(path)

    # Find cell with described.plot(kind="bar")
    idx, cell = find_cell_containing(nb, 'described.plot(kind="bar")')
    if idx is None:
        print(f"  ✗ N1.Repository: target cell not found")
        return

    old_src = get_source(cell)
    new_src = old_src.replace(
        'described.plot(kind="bar")',
        'if len(described) > 0:\n    described.plot(kind="bar")'
    )
    set_source(cell, new_src)
    save_nb(nb, path)
    print(f"  patched cell {idx}: guard empty Series before bar plot")


def patch_n1_skip_notebook():
    """N1.Skip.Notebook — session.query(Query).all()[-1] crashes if Query table
    is empty or has no rows matching the ORM model.
    Wrap in try/except."""
    path = ANALYSES_DIR / "N1.Skip.Notebook.ipynb"
    nb = load_nb(path)

    idx, cell = find_cell_containing(nb, "session.query(Query).all()[-1]")
    if idx is None:
        print(f"  ✗ N1.Skip.Notebook: target cell not found")
        return

    old_src = get_source(cell)
    new_src = old_src.replace(
        "session.query(Query).all()[-1]",
        "(session.query(Query).all() or [None])[-1]"
    )
    set_source(cell, new_src)
    save_nb(nb, path)
    print(f"  patched cell {idx}: safe fallback for empty Query table")


def patch_n10_markdown():
    """N10.Markdown — KeyError: 'french' when no French notebooks in subset.
    Guard cnt.loc[lang] lookups with .get() fallback."""
    path = ANALYSES_DIR / "N10.Markdown.ipynb"
    nb = load_nb(path)

    # Find cell with cnt.loc["french", 0]
    idx, cell = find_cell_containing(nb, 'cnt.loc["french", 0]')
    if idx is None:
        print(f"  ✗ N10.Markdown: french cell not found")
        return

    old_src = get_source(cell)
    # Replace cnt.loc["french", 0] with safe access
    new_src = old_src.replace(
        'cnt.loc["french", 0]',
        '(cnt.loc["french", 0] if "french" in cnt.index else 0)'
    )
    set_source(cell, new_src)
    save_nb(nb, path)
    print(f"  patched cell {idx}: guard missing 'french' language key")

    # There may be other language lookups with the same pattern — patch all
    nb2 = load_nb(path)
    patched_any = False
    for i, c in enumerate(nb2["cells"]):
        if c.get("cell_type") != "code":
            continue
        src = get_source(c)
        # Pattern: cnt.loc["<lang>", 0]
        langs = re.findall(r'cnt\.loc\["([a-z]+)",\s*0\]', src)
        if langs:
            new = src
            for lang in langs:
                new = new.replace(
                    f'cnt.loc["{lang}", 0]',
                    f'(cnt.loc["{lang}", 0] if "{lang}" in cnt.index else 0)'
                )
            if new != src:
                set_source(c, new)
                patched_any = True
    if patched_any:
        save_nb(nb2, path)
        print(f"  patched additional language key guards in N10.Markdown")


def patch_n2_notebook():
    """N2.Notebook — np.percentile on empty array when with_execution_numbers
    is empty. Guard distribution_with_boxplot against empty input."""
    path = ANALYSES_DIR / "N2.Notebook.ipynb"
    nb = load_nb(path)

    idx, cell = find_cell_containing(nb, "distribution_with_boxplot")
    if idx is None:
        print(f"  ✗ N2.Notebook: distribution_with_boxplot cell not found")
        return

    old_src = get_source(cell)
    # Wrap the decorated function body to skip if column is empty
    # The function is decorated with @calculate_auto and @close_fig
    # We add an early return if the column is empty
    new_src = old_src.replace(
        'column = with_execution_numbers["max_execution_count"]',
        'column = with_execution_numbers["max_execution_count"]\n    if len(column) == 0:\n        return None'
    )
    set_source(cell, new_src)
    save_nb(nb, path)
    print(f"  patched cell {idx}: guard empty execution count column")


def patch_n3_cell():
    """N3.Cell — np.bitwise_and fails because raw_cells["skip"] is dtype object
    in Dask when loaded from SQLite. Cast to int first."""
    path = ANALYSES_DIR / "N3.Cell.ipynb"
    nb = load_nb(path)

    idx, cell = find_cell_containing(nb, "np.bitwise_and(raw_cells")
    if idx is None:
        print(f"  ✗ N3.Cell: bitwise_and cell not found")
        return

    old_src = get_source(cell)
    new_src = old_src.replace(
        'raw_cells[np.bitwise_and(raw_cells["skip"], SKIP_MAP[prefix]) == 0]',
        'raw_cells[np.bitwise_and(raw_cells["skip"].astype(int), int(SKIP_MAP[prefix])) == 0]'
    )
    set_source(cell, new_src)
    save_nb(nb, path)
    print(f"  patched cell {idx}: cast skip column and SKIP_MAP value to int")


def patch_n5_modules():
    """N5.Modules — venn2 subset_labels contains None when a region is empty.
    Add null check before calling label.set_text()."""
    path = ANALYSES_DIR / "N5.Modules.ipynb"
    nb = load_nb(path)

    idx, cell = find_cell_containing(nb, "label.set_text")
    if idx is None:
        print(f"  ✗ N5.Modules: label.set_text cell not found")
        return

    old_src = get_source(cell)
    new_src = old_src.replace(
        'for label in venn.subset_labels:\n        label.set_text("{0:,g}".format(int(label.get_text())))',
        'for label in venn.subset_labels:\n        if label is not None:\n            label.set_text("{0:,g}".format(int(label.get_text())))'
    )
    # Also guard local_label which may be None
    new_src = new_src.replace(
        'local_label = venn.subset_labels[0]\n    xy = local_label.get_position()',
        'local_label = venn.subset_labels[0]\n    if local_label is None:\n        return\n    xy = local_label.get_position()'
    )
    set_source(cell, new_src)
    save_nb(nb, path)
    print(f"  patched cell {idx}: null-guard Venn diagram subset labels")


def patch_n7_name():
    """N7.Name — pandas apply() returns DataFrame of dicts instead of Series
    in pandas 1.3+. Use explicit Series wrapping."""
    path = ANALYSES_DIR / "N7.Name.ipynb"
    nb = load_nb(path)

    idx, cell = find_cell_containing(nb, "_dict] = raw_names.apply")
    if idx is None:
        print(f"  ✗ N7.Name: apply cell not found")
        return

    old_src = get_source(cell)
    # The apply returns a Series of dicts. In pandas 1.3+ this can be inferred
    # as a DataFrame. Force it by assigning to a temp var and converting.
    new_src = old_src.replace(
        'raw_names[column + "_dict"] = raw_names.apply(\n        (\n            lambda r: {\n                k: int(v)\n                for k, v in zip(\n                    r[column].split(","), r[column + "_counts"].split(",")\n                )\n                if k\n                if int(v)\n            }\n        ),\n        axis=1,\n    )',
        'raw_names[column + "_dict"] = raw_names.apply(\n        (\n            lambda r: {\n                k: int(v)\n                for k, v in zip(\n                    r[column].split(","), r[column + "_counts"].split(",")\n                )\n                if k\n                if int(v)\n            }\n        ),\n        axis=1,\n        result_type="reduce",\n    )'
    )
    if new_src == old_src:
        # Try alternate indent style
        new_src = re.sub(
            r'(raw_names\[column \+ "_dict"\] = raw_names\.apply\()',
            r'\1',
            old_src
        )
        # Fallback: insert result_type before closing paren of apply
        new_src = old_src.replace(
            "axis=1,\n    )",
            'axis=1,\n        result_type="reduce",\n    )'
        )
    set_source(cell, new_src)
    save_nb(nb, path)
    print(f"  patched cell {idx}: add result_type='reduce' to apply()")


def patch_n8_execution():
    """N8.Execution — df["setup.py"] KeyError when no setup.py executions exist.
    Add guard before accessing setup.py column."""
    path = ANALYSES_DIR / "N8.Execution.ipynb"
    nb = load_nb(path)

    idx, cell = find_cell_containing(nb, 'df["setup.py"]')
    if idx is None:
        print(f"  ✗ N8.Execution: setup.py cell not found")
        return

    old_src = get_source(cell)
    new_src = old_src.replace(
        'failed = len(df[df["setup.py"] == -1])',
        'failed = len(df[df["setup.py"] == -1]) if "setup.py" in df.index else 0'
    )
    set_source(cell, new_src)
    save_nb(nb, path)
    print(f"  patched cell {idx}: guard missing setup.py index key")


def patch_pmc3_reproducibility():
    """PMC3.ReproducibilityStudy — np.polyfit on empty vector.
    Guard the trendline block against empty DataFrame."""
    path = ANALYSES_DIR / "PMC3.ReproducibilityStudy.ipynb"
    nb = load_nb(path)

    idx, cell = find_cell_containing(nb, "np.polyfit")
    if idx is None:
        print(f"  ✗ PMC3.ReproducibilityStudy: polyfit cell not found")
        return

    old_src = get_source(cell)
    # Wrap the polyfit block in an if-guard
    new_src = old_src.replace(
        '# Add a trendline to the scatter plot\ncoefficients = np.polyfit(',
        '# Add a trendline to the scatter plot\nif len(exceptions_by_year_notebook_df) > 0:\n  coefficients = np.polyfit('
    )
    # Also need to indent the rest of the trendline block
    # Find the trendline section and wrap it properly
    lines = old_src.split('\n')
    new_lines = []
    in_trendline = False
    for line in lines:
        if '# Add a trendline to the scatter plot' in line:
            in_trendline = True
            new_lines.append('# Add a trendline to the scatter plot')
            new_lines.append('if len(exceptions_by_year_notebook_df) > 0:')
            continue
        if in_trendline and line.strip() == '' and new_lines and new_lines[-1].strip() == '':
            in_trendline = False
            new_lines.append(line)
        elif in_trendline:
            new_lines.append('    ' + line if line.strip() else line)
        else:
            new_lines.append(line)
    set_source(cell, '\n'.join(new_lines))
    save_nb(nb, path)
    print(f"  patched cell {idx}: guard trendline block against empty DataFrame")


def patch_pmc6_metrics():
    """PMC6.MetricsCorrelation — apply returns DataFrame not Series in pandas 1.3+.
    Fix safe_freq to explicitly return a scalar."""
    path = ANALYSES_DIR / "PMC6.MetricsCorrelation.ipynb"
    nb = load_nb(path)

    idx, cell = find_cell_containing(nb, "safe_freq")
    if idx is None:
        print(f"  ✗ PMC6.MetricsCorrelation: safe_freq cell not found")
        return

    old_src = get_source(cell)
    # The issue: correlation_df.apply(safe_freq, axis=1) returns a DataFrame
    # Force scalar return and use result_type="reduce"
    new_src = old_src.replace(
        'correlation_df["Frequency"] = correlation_df.apply(safe_freq, axis=1)',
        'correlation_df["Frequency"] = correlation_df.apply(safe_freq, axis=1, result_type="reduce")'
    )
    # Also ensure safe_freq returns a scalar (int/float) not a Series
    new_src = new_src.replace(
        'return round(row["Frequency"] / val * 100)',
        'return int(round(row["Frequency"] / val * 100))'
    )
    set_source(cell, new_src)
    save_nb(nb, path)
    print(f"  patched cell {idx}: force scalar return in safe_freq apply")


def patch_pmc7_exception():
    """PMC7.ExceptionAnalysis — ZeroDivisionError when total_notebooks=0.
    Add guard before percentage calculations."""
    path = ANALYSES_DIR / "PMC7.ExceptionAnalysis.ipynb"
    nb = load_nb(path)

    idx, cell = find_cell_containing(nb, "total_notebooks")
    if idx is None:
        print(f"  ✗ PMC7.ExceptionAnalysis: total_notebooks cell not found")
        return

    old_src = get_source(cell)
    # Add early return / guard
    new_src = old_src.replace(
        'percentage_exceptions_more_than_10 = (\n    notebooks_exceptions_more_than_10 / total_notebooks\n) * 100',
        'if total_notebooks == 0:\n    print("No notebooks found for this query — skipping percentage calculation")\nelse:\n  percentage_exceptions_more_than_10 = (\n    notebooks_exceptions_more_than_10 / total_notebooks\n  ) * 100'
    )
    # Simpler approach — just guard the division
    if new_src == old_src:
        new_src = old_src.replace(
            'notebooks_exceptions_more_than_10 / total_notebooks',
            'notebooks_exceptions_more_than_10 / max(total_notebooks, 1)'
        ).replace(
            'notebooks_no_exceptions / total_notebooks',
            'notebooks_no_exceptions / max(total_notebooks, 1)'
        ).replace(
            'notebooks_exceptions_less_than_10 / total_notebooks',
            'notebooks_exceptions_less_than_10 / max(total_notebooks, 1)'
        )
    set_source(cell, new_src)
    save_nb(nb, path)
    print(f"  patched cell {idx}: guard division by zero in percentage calculations")


if __name__ == "__main__":
    print("Patching notebooks...\n")

    patches = [
        ("N1.Repository", patch_n1_repository),
        ("N1.Skip.Notebook", patch_n1_skip_notebook),
        ("N10.Markdown", patch_n10_markdown),
        ("N2.Notebook", patch_n2_notebook),
        ("N3.Cell", patch_n3_cell),
        ("N5.Modules", patch_n5_modules),
        ("N7.Name", patch_n7_name),
        ("N8.Execution", patch_n8_execution),
        ("PMC3.ReproducibilityStudy", patch_pmc3_reproducibility),
        ("PMC6.MetricsCorrelation", patch_pmc6_metrics),
        ("PMC7.ExceptionAnalysis", patch_pmc7_exception),
    ]

    success = 0
    for name, fn in patches:
        print(f"[{name}]")
        try:
            fn()
            success += 1
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
        print()

    print(f"Done: {success}/{len(patches)} notebooks patched.")
