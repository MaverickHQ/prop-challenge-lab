"""E1.2 — the G4 plateau geometry, tested directly.

This replaces coverage lost when the entry gate started refusing the fade:
two integration tests used a fade sweep as their vehicle, and one of them
carried the regression test for a real bug. Re-indexing the grid to a 1-D
chain capped every Chebyshev-1 neighbourhood at 3 members, which made
`plateau_cells=5` unsatisfiable and a GO impossible in every prior run.

Testing the geometry directly is better than testing it through a sweep: it
pins the BUG SHAPE rather than a strategy family that happened to exercise
it, and it cannot be broken again by a family being retired.
"""

from __future__ import annotations

from occams.harness import MCStats
from occams.search import Gates, GridAxis, Sweep, SweepCell, find_winner


def _cell(idx, p_pass=0.70):
    return SweepCell(indices=idx, params={},
                     stats=MCStats(n_runs=100, p_pass=p_pass, p_breach=0.05,
                                   median_days=40, traded_days=60))


def _grid_2d(rows=3, cols=3, p_pass=0.70):
    """A real 2-D grid: range_minutes x k_stop."""
    cells = tuple(_cell((r, c), p_pass) for r in range(rows)
                  for c in range(cols))
    axes = (GridAxis("range_minutes", tuple(range(rows))),
            GridAxis("k_stop", tuple(range(cols))))
    return Sweep(cells, axes, "test")


def _grid_flattened(n=9, p_pass=0.70):
    """The BUG: the same nine cells re-indexed to a 1-D chain."""
    cells = tuple(_cell((i,), p_pass) for i in range(n))
    return Sweep(cells, (GridAxis("flat", tuple(range(n))),), "test")


def test_a_true_2d_interior_cell_has_nine_neighbours():
    from occams.search import _neighbourhood
    sweep = _grid_2d()
    centre = next(c for c in sweep.cells if c.indices == (1, 1))
    assert len(_neighbourhood(centre, sweep)) == 9


def test_the_SAME_cells_flattened_to_1d_have_only_three():
    """The defect in one assertion: nine cells, but a chain neighbourhood
    can never exceed three, so plateau_cells=5 could never be met."""
    from occams.search import _neighbourhood
    sweep = _grid_flattened()
    centre = next(c for c in sweep.cells if c.indices == (4,))
    assert len(_neighbourhood(centre, sweep)) == 3


GATES = Gates(p_pass_min=0.55, edge_vs_null=0.15, p_breach_max=0.30,
              plateau_cells=5, plateau_slack=0.05)


def test_plateau_5_is_satisfiable_on_a_real_grid():
    assert find_winner(_grid_2d(), null_p_pass=0.40, gates=GATES) is not None


def test_plateau_5_is_UNSATISFIABLE_when_the_grid_is_flattened():
    """Proves the bug would still be caught: same cells, same stats, same
    gates — only the geometry differs, and a GO becomes impossible."""
    assert find_winner(_grid_flattened(), null_p_pass=0.40,
                       gates=GATES) is None


def test_an_edge_cell_has_fewer_neighbours_than_an_interior_one():
    from occams.search import _neighbourhood
    sweep = _grid_2d()
    corner = next(c for c in sweep.cells if c.indices == (0, 0))
    centre = next(c for c in sweep.cells if c.indices == (1, 1))
    assert len(_neighbourhood(corner, sweep)) == 4
    assert len(_neighbourhood(centre, sweep)) == 9
