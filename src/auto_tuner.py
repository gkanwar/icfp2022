# Runs automated parameter search using ray to find best blocked solution
import argparse

from ray import air, tune
from ray.air import session
from ray.tune.schedulers import AsyncHyperBandScheduler
from ray.tune.search.ax import AxSearch

import sim
import lang
import paint 

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', type=str, required=True)
    parser.add_argument('-o', '--output', type=str, required=True)
    parser.add_argument('-n', '--num_samples', type=int, default=25)
    args = parser.parse_args()

    
    img = paint.load(args.input)


    def score_cmds(cmds):
        state = sim.State(400, 400, {
            '0': sim.make_filled_block(0, 0, 400, 400, (255,255,255,255))
        })

        moves = lang.parse_lines(cmds)
        res = sim.run_program(state, moves)
        diff_cost = round(paint.diff_cost(img, res['output']))
        return res['cost'] + diff_cost


    def objective(config):
        paint.NBLOCKS = config["num_blocks"]
        
        cmds = paint.solve(img, config["orient"], (config["bleed_a" ], config["bleed_b"]))

        cost = score_cmds(cmds)
        session.report({
            'cost': cost
        })


    search_space = {
        "num_blocks": tune.choice([1, 2, 4, 5, 8, 10, 16, 20, 25]),
        "orient": tune.choice(['vertA', 'vertB', 'horizA', 'horizB']),
        "bleed_a": tune.randint(0,14),
        "bleed_b": tune.randint(0,14),
    }

    algo = AxSearch()
    algo = tune.search.ConcurrencyLimiter(algo, max_concurrent=16)
    scheduler = AsyncHyperBandScheduler()
    
    tuner = tune.Tuner(
        objective,
        run_config=air.RunConfig(
            name="ax",
        ),
        tune_config=tune.TuneConfig(
            metric="cost",
            num_samples=args.num_samples,
            search_alg=algo,
            scheduler=scheduler,
            mode="min",
        ),
        param_space=search_space
    )
    results = tuner.fit()

    # save the version with the lowest cost
    best_config = results.get_best_result().config
    paint.NBLOCKS = best_config["num_blocks"]
    cmds = paint.solve(img, best_config["orient"], (best_config["bleed_a" ], best_config["bleed_b"]))
    with open(args.output, "w") as f:
        f.writelines([c + "\n" for c in cmds])
        
    print(f"Best config: {best_config}")


if __name__ == '__main__':
    main()
