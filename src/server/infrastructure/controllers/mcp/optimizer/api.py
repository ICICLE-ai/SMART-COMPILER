from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated

from mcp.server import FastMCP
from pydantic import Field

from server.tools.program_optimizer.optimizer import CetusOptimizer


def optimize_code_snippet(
    code_snippet: Annotated[str, Field(description="The C source code to optimize with Cetus")],
    optimization_profile: Annotated[
        str,
        Field(
            description=(
                "Cetus optimization profile. Available profiles include parallel, "
                "paw_tiling_nt, paw_tiling_lrw, paw_tiling_fixed32, and reuse_analysis."
            )
        ),
    ] = "parallel",
) -> str:
    """Optimize a C code snippet with Cetus and return the transformed source."""
    with TemporaryDirectory(prefix="smart-compiler-cetus-") as temp_dir:
        work_dir = Path(temp_dir)
        source_path = work_dir / "input.c"
        output_dir = work_dir / "output"
        source_path.write_text(code_snippet)

        result = CetusOptimizer().optimize_file(
            source_path,
            optimization_profile,
            output_dir=output_dir,
        )
        return Path(result.output_path).read_text()


def register_api(server: FastMCP) -> None:
    server.add_tool(optimize_code_snippet)
