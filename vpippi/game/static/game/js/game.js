class CustomMap {
    constructor(ctx, img, foreground_img, width, height, start_x, start_y, walls_array, player) {
        this.ctx = ctx;
        this.player = player;

        this.loadData(img, foreground_img, width, height, start_x, start_y, walls_array);

        this.img.onload = () => {
            this.draw();
        }

        this.isMoving = false;
        this.intervalId = null;
        this.movingFrames = 15;

        this.WALKING_SPEED = 250;
        this.RUNNING_SPEED = 100;
        this.TURNING_SPEED = 50;

        this.turningTime = this.TURNING_SPEED;
        this.movingTime = this.WALKING_SPEED;
        this.drawLoop();
    }

    loadData(img, foreground_img, width, height, start_x, start_y, walls_array) {
        this.img = new Image();
        this.img.src = img;

        this.foreground = new Image();
        if (foreground_img) {
            this.foreground.src = foreground_img;
        }

        this.map_width = width;
        this.map_height = height;
        this.x = start_x;
        this.y = start_y;

        this.walls = walls_array;
        this.doors = {};
        this.items = {};
        this.npcs = {};
    }

    drawLoop() {
        window.requestAnimationFrame(() => {
            this.draw();
            this.drawLoop();
        });
    }

    draw() {
        let block_src_size = this.img.width / this.map_width;
        let block_dst_size = 32;
        console.assert(block_src_size == this.img.height / this.map_height, "Inconsistent block size: " + block_src_size + " vs " + this.img.height / this.map_height);
        let block_ratio = block_src_size / block_dst_size;

        let sWidth = this.ctx.canvas.width * block_ratio;
        let sHeight = this.ctx.canvas.height * block_ratio;
        let sx = this.x / this.map_width * this.img.width - sWidth / 2;
        let sy = this.y / this.map_height * this.img.height - sHeight / 2;

        // Fill the background with black
        this.ctx.fillStyle = "black";
        this.ctx.fillRect(0, 0, this.ctx.canvas.width, this.ctx.canvas.height);

        // Draw the map
        this.ctx.drawImage(this.img, sx, sy, sWidth, sHeight, 0, 0, this.ctx.canvas.width, this.ctx.canvas.height);
        // console.log(this.img, sx, sy, sWidth, sHeight, 0, 0, this.ctx.canvas.width, this.ctx.canvas.height);

        // Draw the player
        this.player.draw();

        // Draw the foreground
        this.ctx.drawImage(this.foreground, sx, sy, sWidth, sHeight, 0, 0, this.ctx.canvas.width, this.ctx.canvas.height);
    }

    move(x, y, player_direction) {
        if (this.isMoving) {
            return;
        }
        this.isMoving = true;
        if (this.player.direction == player_direction) {
            let [next_x, next_y] = this.getFrontPosition();
            if (next_y < 0 || next_x < 0 || this.walls[next_y][next_x] == 1) {
                this.isMoving = false;
                return;
            }
            this.movingAnimation(x, y);
        } else {
            this.turningAnimation(player_direction);
        }
    }

    movingAnimation(x, y) {
        this.player.move_count++;
        executeMultipleTimes(this.movingFrames, this.movingTime / this.movingFrames, () => {
            this.x += x / this.movingFrames;
            this.y += y / this.movingFrames;
        });
        setTimeout(() => {
            this.isMoving = false;
            this.player.move_count++;
        }, this.movingTime);
    }

    turningAnimation(player_direction) {
        this.player.direction = player_direction;
        setTimeout(() => {
            this.isMoving = false;
        }, this.turningTime);
    }

    getFrontPosition() {
        let x = Math.round(this.x);
        let y = Math.round(this.y);
        switch (this.player.direction) {
            case 0:
                y -= 1;
                break;
            case 1:
                y += 1;
                break;
            case 2:
                x -= 1;
                break;
            case 3:
                x += 1;
                break;
        }
        return [x, y];
    }

    getDialog(pos) {
        let [x, y] = pos;
        if (this.npcs[y + '_' + x] != undefined) {
             return this.npcs[y + '_' + x];
        } else {
            return this.items[y + '_' + x];
        }
    }

    moveLeft() {
        this.move(-1, 0, 2);
    }
    moveRight() {
        this.move(1, 0, 3);
    }
    moveUp() {
        this.move(0, -1, 0);
    }
    moveDown() {
        this.move(0, 1, 1);
    }

    canMoveLeft() {
        return this.x > 0;
    }
    canMoveRight() {
        return this.x < this.map_width;
    }
    canMoveUp() {
        return this.y > 0;
    }
    canMoveDown() {
        return this.y < this.map_height;
    }

    isDoor() {
        let x = Math.round(this.x);
        let y = Math.round(this.y);        
        return this.doors[y + '_' + x];
    }
    
    drawPos() {
        let x = Math.round(this.x);
        let y = Math.round(this.y);        
        $('#pos').text(y + '_' + x);
    }
}

class Player {
    constructor(ctx, direction, url) {
        this.ctx = ctx;
        this.img = new Image();
        this.img.src = url;
        this.direction = direction;
        this.move_count = 0;

        this.img.onload = () => {
            this.player_width = Math.floor(this.img.width / 4);
            this.player_height = Math.floor(this.img.height / 4);
            this.draw();
        };
    }

    draw() {
        let sx = Math.round(this.move_count % 4 * this.player_width);
        let sy = Math.round(this.direction * this.player_height);
        let dWidth = 32;
        let dHeight = this.player_height * 32 / this.player_width;
        let dx = this.ctx.canvas.width / 2;
        let dy = this.ctx.canvas.height / 2 - (dHeight - dWidth);
        this.ctx.drawImage(this.img, sx, sy, this.player_width, this.player_height, dx, dy, dWidth, dHeight);
    }
}

class Controller { 
    constructor(map_img, walls_array, width, height, player_spritesheet, x, y, orientation) {
        this.canvas = document.getElementById('game_canvas');
        this.canvas.width = document.body.clientWidth;
        this.canvas.height = document.body.clientHeight;
        this.movement_flag = true;
        this.ctx = this.canvas.getContext('2d');
        this.player_url = player_spritesheet;

        this.player = new Player(this.ctx, orientation, this.player_url);
        this.map = new CustomMap(this.ctx, map_img, null, width, height, x, y, walls_array, this.player);

        this.movment_history = [];
        $(document).keydown((e) => {
            if (e.keyCode >= 37 && e.keyCode <= 40 && this.movement_flag) {
                removeFromMemory(this.movment_history, e.keyCode);
                addToMemory(this.movment_history, e.keyCode);
            }

            if (e.keyCode == 17) { // ctrl
                this.map.movingTime = this.map.RUNNING_SPEED;
                this.map.turningTime = 0;
            }

            if (e.keyCode == 32 || e.keyCode == 13) { // space or enter
                let pos = this.map.getFrontPosition();
                let text = this.map.getDialog(pos);
                let dialog = $('#popup');
                console.log(text);
                console.log(text != undefined);
                if (!this.movement_flag) {
                    dialog.hide();
                    this.movement_flag = true;
                } else if (text != undefined && this.movement_flag){
                    dialog.text(text);
                    dialog.show();
                    this.movement_flag = false;
                    this.movment_history = [];
                } 
            }
        });
        
        $(document).keyup((e) => {
            if (e.keyCode >= 37 && e.keyCode <= 40) {
                removeFromMemory(this.movment_history, e.keyCode);
            }
            
            if (e.keyCode == 17) { // ctrl
                this.map.movingTime = this.map.WALKING_SPEED;
                this.map.turningTime = this.map.TURNING_SPEED;
            }
            
            // if (e.keyCode == 32 || e.keyCode == 13) { // space or enter
            //     // disappear popup
            // }
        });

        this.movementLoop();
    }

    movementLoop() {
        window.requestAnimationFrame(() => {
            if (this.movment_history.length > 0) {
                let last = this.movment_history[this.movment_history.length - 1];
                if (last == 37) {
                    this.map.moveLeft();
                } else if (last == 38) {
                    this.map.moveUp();
                } else if (last == 39) {
                    this.map.moveRight();
                } else if (last == 40) {
                    this.map.moveDown();
                }
                let door = this.map.isDoor();
                // if (door != undefined) {
                //     $.getJSON(door.json, (data) => {
                //         console.log(door);
                //         console.log(data);
                //         data.start_x = door.start_x;
                //         data.start_y = door.start_y;
                //         data.player_direction = door.player_direction;
                //         this.map.loadData(data);
                //     });
                // }
                this.map.drawPos();
            }
            this.movementLoop();
        });
    }
}

function removeFromMemory(arr, keyCode) {
    let index = arr.indexOf(keyCode);
    if (index > -1) {
        arr.splice(index, 1);
    }
    return arr;
}

function addToMemory(arr, keyCode) {
    arr.push(keyCode);
    return arr;
}

function executeMultipleTimes(times, delay, fn) {
    let counter = 0;
    const intervalId = setInterval(() => {
        fn();
        counter++;
        if (counter === times) {
            clearInterval(intervalId);
        }
    }, delay);
}