import sys
from game import Game


def main():
    verbose = "--verbose" in sys.argv

    print("=" * 60)
    print("FRIGATE — Hex Space Combat")
    if verbose:
        print("(verbose mode)")
    print("=" * 60)

    game = Game(verbose=verbose)
    game.setup()

    from display import display_board, display_ship_status
    display_board(game.board, game.players)
    for player in game.players:
        display_ship_status(player)

    while not game.is_over:
        game.run_round()

    print("\nGame Over!")


if __name__ == "__main__":
    main()
