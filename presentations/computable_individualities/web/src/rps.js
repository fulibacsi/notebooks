const HANDS = ['r', 'p', 's'];


// cartesian product
function product(arr, repeat) {
    const f = (a, b) => [].concat(...a.map(d => b.map(e => [].concat(d, e))));
    const cartesian = (a, b, ...c) => (b ? cartesian(f(a, b), ...c) : a);

    var variations = []
    for (i = 1; i < repeat + 1; i++) {
        // generate arrays
        var arrays = [];
        for (j = 0; j < i; j++) {
            arrays.push(arr);
        }

        // generate products
        var variation = [];
        cartesian(...arrays).forEach(element => {
            if (Array.isArray(element)) variation.push(element.join(''));
            else variation.push(element);
        });

        variations = variations.concat(variation);
    }

    return variations;
}


function random_choice(list) {
    return list[Math.floor(Math.random() * list.length)];
}


class RPS {

    constructor(mode='naive', memsize=1) {
        this.beat = {'r': 'p',
                     'p': 's',
                     's': 'r'}
        this.pool = HANDS;
        this.mode = mode;
        this.game_log = [];

        if (this.mode == 'stateful') {
            this.memsize = Math.min(memsize, 3);
            this.pool = this.generate_stateful_pool();
            this.state = null;
        }

    }

    generate_stateful_pool(self) {
        var keys = {};
        product(HANDS, this.memsize).forEach(element => {
            keys[element] = HANDS;
        });

        return keys;
    }

    play(player) {
        var ai = this.beat[this.predict()];
        var result = this.result(ai, player);

        this.log_game(ai, player, result);
        this.learn(ai, player);

        return result;
    }

    predict() {
        if (this.mode == 'null')
            return this.random_choice(HANDS);
        if (this.mode == 'naive')
            return random_choice(this.pool);
        if (this.mode == 'stateful' & this.state !== null)
            return random_choice(this.pool[this.state]);

        return this.random()
    }

    result(ai, player) {
        // tie
        if (ai == player) return 0;
        // win
        if (this.beat[ai] == player) return 1;
        // lose
        return -1;
    }

    learn(ai, player) {
        if (this.mode == 'naive')
            this.pool.push(player);

        else if (self.mode == 'stateful') {
            if (this.state != null) {
                this.pool[this.state].push(player)
            }
            this.state = this.update_state(ai, player)
        }
    }

    update_state(ai, player) {
        if (this.mode == 'stateful') {
            var state;
            if (this.state == null) state = '';
            state += player;

            return state.slice(-this.memsize);
        }
    }

    log_game(ai, player, result) {
        var log = {'ai': ai,
                   'player': player,
                   'result': result};
        this.game_log.push(log);
    }

}
