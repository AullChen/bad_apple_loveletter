# A Love Letter but Bad Apple

On Valentine's Day, couples go outside having wonderful time while singles stay lonely and try to find something could pass the time. When watching videos on bilibili, I am often tricked by those have different start but end with [Bad Apple!!](https://en.wikipedia.org/wiki/Bad_Apple!!) video. No, I'm not angry but feel interesting. So why not create a cyber love letter end with *Bad Apple* too?

The program is inspired by [mon/bad_apple_virus: Bad Apple using Windows windows](https://github.com/mon/bad_apple_virus), and refactoring with python in order to finish my schoolwork at the same time.  

## How it works?

- `letter.py` is responsible for displaying love letter, which could be freely created. However, to make the transition smoother, a white curtain at the end is recommended.
- `main.py` includes two parts:
  -  the functions used to show *Bad Apple* 
  -  the `main()` to connect letter and show for the final display.
- `/assets` folder includes video data `boxes.bin` and `bad apple.ogg` which got from [bad_apple_virus](https://github.com/mon/bad_apple_virus), and `tech_love.json` for love letter.

## Problems remained

- Python's performance is not as good as Rust, so the animation part of the screen will become slower, resulting in a mismatch between audio and display screen. The current solution is to adjust the total duration of the screen to be consistent with the audio.
- The end of the letter part will result in the termination of the audio, so there is a clear gap between the two parts in order to avoid it. I think it is caused by `pygame`.

## Usage

1. Install dependencies

   ```bash
   pip install -r requirements.txt
   ```

2. Open folder `/src` and run `main.py`

   ```bash
   python main.py
   ```

   

