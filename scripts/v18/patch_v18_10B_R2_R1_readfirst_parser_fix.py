from pathlib import Path

run_path = Path(r"D:\us-tech-quant\scripts\v18\run_v18_10B_R2_factor_research_daily_chain.ps1")

text = run_path.read_text(encoding="utf-8-sig")

target = "function Get-ReadFirstValue"
start = text.find(target)
if start < 0:
    raise SystemExit("FUNCTION_GET_READFIRSTVALUE_NOT_FOUND")

brace_start = text.find("{", start)
if brace_start < 0:
    raise SystemExit("FUNCTION_OPEN_BRACE_NOT_FOUND")

depth = 0
end = None
for i in range(brace_start, len(text)):
    ch = text[i]
    if ch == "{":
        depth += 1
    elif ch == "}":
        depth -= 1
        if depth == 0:
            end = i + 1
            break

if end is None:
    raise SystemExit("FUNCTION_CLOSE_BRACE_NOT_FOUND")

new_func = r'''function Get-ReadFirstValue {
    param(
        [string]$Path,
        [string]$Key
    )

    if (-not (Test-Path $Path)) {
        return ""
    }

    $Target = $Key.Trim()
    if (-not $Target.EndsWith(":")) {
        $Target = $Target + ":"
    }

    $Lines = Get-Content $Path -Encoding UTF8

    for ($i = 0; $i -lt $Lines.Count; $i++) {
        $Line = $Lines[$i].Trim()

        # Format A:
        # STATUS: OK_FORWARD_RETURN_FILLER_READY
        if ($Line.StartsWith($Target)) {
            $Value = $Line.Substring($Target.Length).Trim()
            if ($Value -ne "") {
                return $Value
            }
        }

        # Format B:
        # STATUS:
        # OK_FORWARD_RETURN_FILLER_READY
        if ($Line -eq $Target) {
            for ($j = $i + 1; $j -lt $Lines.Count; $j++) {
                $Next = $Lines[$j].Trim()
                if ($Next -ne "") {
                    return $Next
                }
            }
        }
    }

    return ""
}'''

text2 = text[:start] + new_func + text[end:]
run_path.write_text(text2, encoding="utf-8")

print("PATCHED_READFIRST_PARSER:", run_path)
