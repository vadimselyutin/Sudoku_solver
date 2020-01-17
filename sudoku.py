import numpy as np

def matrix_to_puzzle(matrix):
    rows = [' {}  {}  {} | {}  {}  {} | {}  {}  {}'.format(*x).replace('0', '.') for x in matrix]
    rows.insert(6, '---------+---------+---------')
    rows.insert(3, '---------+---------+---------')
    return '\n'.join(rows)

def puzzle_to_matirx(puzzle):
    vector = [x for x in puzzle.values()]
    return np.array(vector).astype(int).reshape([9, 9])

def solve_sudoku(sudoku_matrix):
    puzzle = matrix_to_puzzle(sudoku_matrix)
    try:
        solution = solve_puzzle(puzzle)
    except TypeError as e:
        raise ValueError('An error in sudoku solving engine. Please check your CV algorithm!') from None
    return puzzle_to_matirx(solution)

################### The code above converts matrix to string and back

################### The code below is taken from https://medium.com/@neshpatel/solving-sudoku-part-i-7c4bb3097aa7


def sudoku_reference():
    """Gets a tuple of reference objects that are useful for describing the Sudoku grid."""
    
    def cross(str_a, str_b):
        """Cross product (concatenation) of two strings A and B."""
        return [a + b for a in str_a for b in str_b]

    all_rows = 'ABCDEFGHI'
    all_cols = '123456789'

    # Build up list of all cell positions on the grid
    coords = cross(all_rows, all_cols)
    # print(len(coords))  # 81

    # Get the units for each row
    row_units = [cross(row, all_cols) for row in all_rows]
    # print(row_units[0])  # ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9']

    # Do it in reverse to get the units for each column
    col_units = [cross(all_rows, col) for col in all_cols]
    # print(col_units[0])  # ['A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1', 'I1']

    box_units = [cross(row_square, col_square) for row_square in ['ABC', 'DEF', 'GHI'] for col_square in ['123', '456', '789']]
    # print(box_units[0])   # ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3']

    all_units = row_units + col_units + box_units  # Add units together
    groups = {}

    # For each cell, get the each unit that the cell is part of (3 per cell)
    groups['units'] = {pos: [unit for unit in all_units if pos in unit] for pos in coords}
    # print(units['A1'])  # 3 Units of length 9 for each cell

    # For each cell get the list of peers to that position
    groups['peers'] = {pos: set(sum(groups['units'][pos], [])) - {pos} for pos in coords}
    # print(peers['A1'])  # Peer cells for the position, length 20 for each cell
    
    return coords, groups, all_units


def parse_puzzle(puzzle, digits='123456789', nulls='0.'):
    """
    Parses a string describing a Sudoku puzzle board into a dictionary with each cell mapped to its relevant
    coordinate, i.e. A1, A2, A3...
    """

    # Serialise the input into a string, let the position define the grid location and .0 can be empty positions
    # Ignore any characters that aren't digit input or nulls
    flat_puzzle = ['.' if char in nulls else char for char in puzzle if char in digits + nulls]

    if len(flat_puzzle) != 81:
        raise ValueError('Input puzzle has %s grid positions specified, must be 81. Specify a position using any '
                         'digit from 1-9 and 0 or . for empty positions.' % len(flat_puzzle))

    coords, groups, all_units = sudoku_reference()

    # Turn the list into a dictionary using the coordinates as the keys
    return dict(zip(coords, flat_puzzle))

def validate_sudoku(puzzle):
    """Checks if a completed Sudoku puzzle has a valid solution."""
    
    if puzzle is None:
        return False
      
    coords, groups, all_units = sudoku_reference()
    full = [str(x) for x in range(1, 10)]  # Full set, 1-9 as strings
    
    # Checks if all units contain a full set
    return all([sorted([puzzle[cell] for cell in unit]) == full for unit in all_units])


def solve_puzzle(puzzle):
    """Solves a Sudoku puzzle from a string input."""
    digits = '123456789'  # Using a string here instead of a list

    coords, groups, all_units = sudoku_reference()
    input_grid = parse_puzzle(puzzle)
    input_grid = {k: v for k, v in input_grid.items() if v != '.'}  # Filter so we only have confirmed cells
    output_grid = {cell: digits for cell in coords}  # Create a board where all digits are possible in each cell

    def confirm_value(grid, pos, val):
        """Confirms a value by eliminating all other remaining possibilities."""
        remaining_values = grid[pos].replace(val, '')  # Possibilities we can eliminate due to the confirmation
        for val in remaining_values:
            grid = eliminate(grid, pos, val)
        return grid

    def eliminate(grid, pos, val):
        """Eliminates `val` as a possibility from all peers of `pos`."""

        if grid is None:  # Exit if grid has already found a contradiction
            return None

        if val not in grid[pos]:  # If we have already eliminated this value we can exit
            return grid

        grid[pos] = grid[pos].replace(val, '')  # Remove the possibility from the given cell

        if len(grid[pos]) == 0:  # If there are no remaining possibilities, we have made the wrong decision
            return None
        elif len(grid[pos]) == 1:  # We have confirmed the digit and so can remove that value from all peers now
            for peer in groups['peers'][pos]:
                grid = eliminate(grid, peer, grid[pos])  # Recurses, propagating the constraint
                if grid is None:  # Exit if grid has already found a contradiction
                    return None

        # Check for the number of remaining places the eliminated digit could possibly occupy
        for unit in groups['units'][pos]:
            possibilities = [p for p in unit if val in grid[p]]

            if len(possibilities) == 0:  # If there are no possible locations for the digit, we have made a mistake
                return None
            # If there is only one possible position and that still has multiple possibilities, confirm the digit
            elif len(possibilities) == 1 and len(grid[possibilities[0]]) > 1:
                if confirm_value(grid, possibilities[0], val) is None:
                    return None

        return grid

    # First pass of constraint propagation
    for position, value in input_grid.items():  # For each value we're given, confirm the value
        output_grid = confirm_value(output_grid, position, value)

    if validate_sudoku(output_grid):  # If successful, we can finish here
        return output_grid

    def guess_digit(grid):
        """Guesses a digit from the cell with the fewest unconfirmed possibilities and propagates the constraints."""

        if grid is None:  # Exit if grid already compromised
            return None

        # Reached a valid solution, can end
        if all([len(possibilities) == 1 for cell, possibilities in grid.items()]):
            return grid

        # Gets the coordinate and number of possibilities for the cell with the fewest remaining possibilities
        n, pos = min([(len(possibilities), cell) for cell, possibilities in grid.items() if len(possibilities) > 1])

        for val in grid[pos]:
            # Run the constraint propagation, but copy the grid as we will try many adn throw the bad ones away.
            # Recursively guess digits until its complete and there's a valid solution
            solution = guess_digit(confirm_value(grid.copy(), pos, val))
            if solution is not None:
                return solution

    output_grid = guess_digit(output_grid)
    return output_grid