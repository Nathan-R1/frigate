import argparse
from game import Game


def main():
    parser = argparse.ArgumentParser(description="FRIGATE — Hex Space Combat")
    parser.add_argument("--verbose", action="store_true", help="Show AI debug info")
    parser.add_argument("--no-targeting", action="store_true", help="Use text input instead of interactive targeting")
    args = parser.parse_args()

    game = Game(verbose=args.verbose, no_targeting=args.no_targeting)
    game.setup()
    game.pregame_phase()
    game._render()

    while not game.is_over:
        game.run_turn()

    game.screen.render(game._build_display())
    print("\nGame Over!")


if __name__ == "__main__":
    main()
