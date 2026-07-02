import streamlit as st
import numpy as np
import random
import time

# ---------- Tetris constants ----------
BOARD_WIDTH = 10
BOARD_HEIGHT = 20
CELL_SIZE = 30

SHAPES = {
    "I": [[1,1,1,1]],
    "O": [[1,1],[1,1]],
    "T": [[0,1,0],[1,1,1]],
    "S": [[0,1,1],[1,1,0]],
    "Z": [[1,1,0],[0,1,1]],
    "J": [[1,0,0],[1,1,1]],
    "L": [[0,0,1],[1,1,1]],
}
SHAPE_COLORS = {
    "I": "#00f0f0", "O": "#f0f000", "T": "#a000f0",
    "S": "#00f000", "Z": "#f00000", "J": "#0000f0", "L": "#f0a000",
}

# ---------- Game logic ----------
def new_board():
    return np.zeros((BOARD_HEIGHT, BOARD_WIDTH), dtype=int)

def random_piece():
    name = random.choice(list(SHAPES.keys()))
    return name, [row[:] for row in SHAPES[name]]

def rotate(shape):
    return [list(row) for row in zip(*shape[::-1])]

def check_collision(board, shape, x, y):
    for dy, row in enumerate(shape):
        for dx, cell in enumerate(row):
            if cell:
                nx, ny = x + dx, y + dy
                if nx < 0 or nx >= BOARD_WIDTH or ny >= BOARD_HEIGHT or ny < 0:
                    return True
                if ny < len(board) and board[ny][nx]:
                    return True
    return False

def merge(board, shape, x, y, color_id):
    for dy, row in enumerate(shape):
        for dx, cell in enumerate(row):
            if cell:
                board[y + dy][x + dx] = color_id

def clear_lines(board):
    cleared = 0
    new_b = [row for row in board if any(cell == 0 for cell in row)]
    cleared = BOARD_HEIGHT - len(new_b)
    while len(new_b) < BOARD_HEIGHT:
        new_b.insert(0, [0] * BOARD_WIDTH)
    return np.array(new_b), cleared

COLOR_MAP = [0] + [i + 2 for i in range(7)]
COLOR_VALUES = {
    0: "#1a1a2e",
    1: "#2a2a3e",
    2: "#00f0f0", 3: "#f0f000", 4: "#a000f0",
    5: "#00f000", 6: "#f00000", 7: "#0000f0", 8: "#f0a000",
}

# ---------- Streamlit app ----------
st.set_page_config(page_title="Tetris", layout="centered")
st.title("🧱 Tetris - Streamlit")

if "board" not in st.session_state:
    st.session_state.board = new_board()
    st.session_state.score = 0
    st.session_state.level = 1
    st.session_state.game_over = False
    st.session_state.curr_name, st.session_state.curr_shape = random_piece()
    st.session_state.curr_x = BOARD_WIDTH // 2 - len(st.session_state.curr_shape[0]) // 2
    st.session_state.curr_y = 0
    st.session_state.next_name, st.session_state.next_shape = random_piece()
    st.session_state.last_time = time.time()
    st.session_state.paused = False
    st.session_state.lines = 0
    st.session_state.color_ids = {name: i + 1 for i, name in enumerate(SHAPES.keys())}
    st.session_state.hold_name = None
    st.session_state.hold_used = False
    st.session_state.bag = []
    st.session_state.drop_interval = 0.5

# --- Bag randomizer ---
def next_from_bag():
    if not st.session_state.bag:
        st.session_state.bag = list(SHAPES.keys())
        random.shuffle(st.session_state.bag)
    return st.session_state.bag.pop()

def spawn_piece():
    if st.session_state.game_over:
        return
    name = st.session_state.next_name
    shape = st.session_state.next_shape
    st.session_state.curr_name = name
    st.session_state.curr_shape = shape
    st.session_state.curr_x = BOARD_WIDTH // 2 - len(shape[0]) // 2
    st.session_state.curr_y = 0
    nname = next_from_bag()
    st.session_state.next_name = nname
    st.session_state.next_shape = [row[:] for row in SHAPES[nname]]
    st.session_state.hold_used = False

    if check_collision(st.session_state.board, shape,
                       st.session_state.curr_x, st.session_state.curr_y):
        st.session_state.game_over = True

def hard_drop():
    if st.session_state.game_over or st.session_state.paused:
        return
    while not check_collision(st.session_state.board, st.session_state.curr_shape,
                               st.session_state.curr_x, st.session_state.curr_y + 1):
        st.session_state.curr_y += 1
    lock_piece()

def lock_piece():
    name = st.session_state.curr_name
    cid = st.session_state.color_ids[name]
    merge(st.session_state.board, st.session_state.curr_shape,
          st.session_state.curr_x, st.session_state.curr_y, cid)
    board, cleared = clear_lines(st.session_state.board)
    st.session_state.board = board
    if cleared:
        st.session_state.lines += cleared
        pts = {1: 100, 2: 300, 3: 500, 4: 800}.get(cleared, 100) * st.session_state.level
        st.session_state.score += pts
        st.session_state.level = st.session_state.lines // 10 + 1
        st.session_state.drop_interval = max(0.05, 0.5 - (st.session_state.level - 1) * 0.03)
    spawn_piece()

def move(dx, dy):
    if st.session_state.game_over or st.session_state.paused:
        return
    if not check_collision(st.session_state.board, st.session_state.curr_shape,
                            st.session_state.curr_x + dx, st.session_state.curr_y + dy):
        st.session_state.curr_x += dx
        st.session_state.curr_y += dy
    elif dy == 1:
        lock_piece()

def rotate_piece():
    if st.session_state.game_over or st.session_state.paused:
        return
    new_shape = rotate(st.session_state.curr_shape)
    if not check_collision(st.session_state.board, new_shape,
                            st.session_state.curr_x, st.session_state.curr_y):
        st.session_state.curr_shape = new_shape

def hold_piece():
    if st.session_state.hold_used or st.session_state.game_over:
        return
    name = st.session_state.curr_name
    if st.session_state.hold_name is None:
        st.session_state.hold_name = name
        spawn_piece()
    else:
        prev_name = st.session_state.hold_name
        st.session_state.hold_name = name
        st.session_state.curr_name = prev_name
        st.session_state.curr_shape = [row[:] for row in SHAPES[prev_name]]
        st.session_state.curr_x = BOARD_WIDTH // 2 - len(st.session_state.curr_shape[0]) // 2
        st.session_state.curr_y = 0
    st.session_state.hold_used = True

# --- Render board ---
def render_board():
    board = st.session_state.board.copy()
    if not st.session_state.game_over:
        shape = st.session_state.curr_shape
        cid = st.session_state.color_ids[st.session_state.curr_name]
        for dy, row in enumerate(shape):
            for dx, cell in enumerate(row):
                if cell:
                    bx, by = st.session_state.curr_x + dx, st.session_state.curr_y + dy
                    if 0 <= by < BOARD_HEIGHT and 0 <= bx < BOARD_WIDTH:
                        board[by][bx] = cid
    return board

def draw_grid():
    board = render_board()
    html = '<div style="display:grid;grid-template-columns:repeat(10,30px);gap:1px;background:#333;padding:1px;border:2px solid #555;border-radius:4px">'
    for y in range(BOARD_HEIGHT):
        for x in range(BOARD_WIDTH):
            c = board[y][x]
            color = COLOR_VALUES.get(c, "#1a1a2e")
            html += f'<div style="width:{CELL_SIZE}px;height:{CELL_SIZE}px;background:{color};border-radius:2px"></div>'
    html += "</div>"
    return html

def draw_mini(shape, name=None):
    color = COLOR_VALUES.get(st.session_state.color_ids.get(name, 0), "#1a1a2e") if name else "#f0f"
    html = '<div style="display:grid;gap:1px;background:#444;padding:1px;border-radius:3px">'
    rows = len(shape)
    cols = len(shape[0]) if shape else 1
    html += f'grid-template-columns:repeat({cols},20px)'
    html += '">'
    for row in shape:
        for cell in row:
            c = color if cell else "#1a1a2e"
            html += f'<div style="width:20px;height:20px;background:{c};border-radius:2px"></div>'
    html += "</div>"
    return html

# --- Keyboard capture ---
def keyboard_capture():
    js = """
<script>
const keyMap = {
    'ArrowLeft': 'LEFT', 'ArrowRight': 'RIGHT', 'ArrowDown': 'DOWN',
    'ArrowUp': 'UP', ' ': 'SPACE', 'c': 'HOLD', 'p': 'PAUSE', 'r': 'RESET'
};
function handleKey(e) {
    const action = keyMap[e.key];
    if (action) {
        e.preventDefault();
        const div = document.createElement('div');
        div.id = 'tetris-key-' + Date.now();
        div.textContent = action;
        div.style.display = 'none';
        document.body.appendChild(div);
    }
}
document.addEventListener('keydown', handleKey);
</script>
"""
    return st.components.v1.html(js, height=0)

# --- Main loop ---
st.markdown("""
<style>
    .stApp { background: #0f0f23; color: #ccc; }
    .stButton>button { width: 100%; }
    div[data-testid="column"] { padding: 0 4px; }
    .info-box { background: #1a1a2e; border: 1px solid #333; border-radius: 8px; padding: 12px; margin: 4px 0; }
    .game-title { color: #00f0f0; font-size: 24px; font-weight: bold; text-align: center; }
    .stat-label { color: #888; font-size: 12px; }
    .stat-value { color: #fff; font-size: 20px; font-weight: bold; }
    .controls { color: #666; font-size: 11px; text-align: center; margin-top: 8px; }
    .controls kbd { background: #2a2a3e; padding: 2px 6px; border-radius: 3px; border: 1px solid #555; color: #ccc; }
</style>
""", unsafe_allow_html=True)

keyboard_capture()

# Check for key input via query params or text input trick
# Use a hidden text input to capture keys
key_result = st.text_input("key", "", key="key_input", label_visibility="collapsed",
                            placeholder="", help="Focus here and use arrow keys")

if key_result:
    action = key_result.strip()
    st.session_state["key_input"] = ""
    if action == "LEFT":
        move(-1, 0)
    elif action == "RIGHT":
        move(1, 0)
    elif action == "DOWN":
        move(0, 1)
    elif action == "UP":
        rotate_piece()
    elif action == "SPACE":
        hard_drop()
    elif action == "HOLD":
        hold_piece()
    elif action == "PAUSE":
        st.session_state.paused = not st.session_state.paused
    elif action == "RESET":
        for k in list(st.session_state.keys()):
            if k != "key_input":
                del st.session_state[k]
        st.rerun()

# --- Auto gravity ---
if not st.session_state.game_over and not st.session_state.paused:
    now = time.time()
    if now - st.session_state.last_time > st.session_state.drop_interval:
        st.session_state.last_time = now
        move(0, 1)
        st.rerun()

# --- Layout ---
left, center, right = st.columns([1, 2, 1])

with left:
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.markdown('<div class="stat-label">HOLD</div>', unsafe_allow_html=True)
    if st.session_state.hold_name:
        html = draw_mini(SHAPES[st.session_state.hold_name], st.session_state.hold_name)
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.markdown('<div style="width:60px;height:60px;background:#1a1a2e;border-radius:3px"></div>',
                    unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.markdown('<div class="stat-label">NEXT</div>', unsafe_allow_html=True)
    html = draw_mini(st.session_state.next_shape, st.session_state.next_name)
    st.markdown(html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with center:
    st.markdown(f'<div class="game-title">TETRIS</div>', unsafe_allow_html=True)
    board_html = draw_grid()
    st.markdown(board_html, unsafe_allow_html=True)

    if st.session_state.game_over:
        st.markdown('<div style="text-align:center;color:#f00;font-size:24px;font-weight:bold;margin-top:8px">GAME OVER</div>',
                    unsafe_allow_html=True)
    elif st.session_state.paused:
        st.markdown('<div style="text-align:center;color:#ff0;font-size:20px;font-weight:bold;margin-top:8px">PAUSED</div>',
                    unsafe_allow_html=True)

with right:
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.markdown('<div class="stat-label">SCORE</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="stat-value">{st.session_state.score:,}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.markdown('<div class="stat-label">LEVEL</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="stat-value">{st.session_state.level}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.markdown('<div class="stat-label">LINES</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="stat-value">{st.session_state.lines}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- Button controls ---
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    if st.button("◀", use_container_width=True):
        move(-1, 0); st.rerun()
with col2:
    if st.button("▶", use_container_width=True):
        move(1, 0); st.rerun()
with col3:
    if st.button("▲\n회전", use_container_width=True):
        rotate_piece(); st.rerun()
with col4:
    if st.button("▼", use_container_width=True):
        move(0, 1); st.rerun()
with col5:
    if st.button("⬇\n드롭", use_container_width=True):
        hard_drop(); st.rerun()

c1, c2, c3 = st.columns(3)
with c1:
    if st.button("H (홀드)", use_container_width=True):
        hold_piece(); st.rerun()
with c2:
    label = "▶ 재개" if st.session_state.paused else "⏸ 일시정지"
    if st.button(label, use_container_width=True):
        st.session_state.paused = not st.session_state.paused; st.rerun()
with c3:
    if st.button("🔄 새 게임", use_container_width=True):
        for k in list(st.session_state.keys()):
            if k != "key_input":
                del st.session_state[k]
        st.rerun()

st.markdown("""
<div class="controls">
    <kbd>←</kbd> <kbd>→</kbd> 이동 · <kbd>↑</kbd> 회전 · <kbd>↓</kbd> 내리기<br>
    <kbd>Space</kbd> 하드드롭 · <kbd>C</kbd> 홀드 · <kbd>P</kbd> 일시정지 · <kbd>R</kbd> 리셋
</div>
""", unsafe_allow_html=True)
