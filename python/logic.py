import unicodedata
import re
import json
import ast
from difflib import SequenceMatcher
import logging

logger = logging.getLogger("mesbot-logic")








COMMAND_LEXICON = {
    "FORWARD": [
        "adelante","avanza","sigue","recto","frente","directo","ve hacia adelante",
        "continuar","seguir","para adelante","alante","adelanti","adelande",
        "adelant",
        "forward","go forward","ahead","move forward","straight",
        
        "elefante", "diamante", "volante", "delante", "levante"
    ],
    "BACKWARD": [
        "atras","atr\u00e1s","reversa","retrocede","hacia atras","hacia atr\u00e1s","retroceso",
        "pa tras","patras","pa'tras","atraz","adtraz","atrasi",
        "retroceder",
        "back","go back","reverse","move back","backward",
        
        "capaz", "fugaz", "audaz", "letras", "mientras"
    ],
    "LEFT": [
        "izquierda","gira a la izquierda","a la izquierda","izq","izda",
        "isquierda","izkierda","iskierda","izqierda","isquielda",
        "vizquierda","disquierda","misquierda","pisquierda","izquierdo","quierdo","quierdas",
        "lizquierda","fisquierda",
        "turn left","left","go left","to the left",
        
        "piedra", "pierna", "mierda", "cuerda", "hiedra"
    ],
    "RIGHT": [
        "derecha","gira a la derecha","a la derecha","der","dcha","drecha",
        "dereca","dereja","deresha","decha","de recha","derech",
        "derecho", 
        "turn right","right","go right","to the right",
        
        "brecha", "flecha", "cosecha", "estrecha"
    ],
    "STOP": [
        "detener","detente","parar","alto","quieto","detente ya","stóp",
        "retener","obtener","mantener",
        "estop","stop","freeze",
        
        "salto", "falto", "pasto", "gasto", "nieta", "aprieta"
    ],
}

def _strip_accents(s: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFKD", s) if not unicodedata.combining(ch))

def _norm(s: str) -> str:
    if not s: return ""
    return _strip_accents(re.sub(r'\s+', ' ', s.strip().lower()))

def _similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()

_NORM_PHRASES: dict[str, str] = {}
for c, vs in COMMAND_LEXICON.items():
    for v in vs: _NORM_PHRASES[_norm(v)] = c

def interpret_command(text: str, fuzzy_threshold: float = 0.88) -> list[str]:
    
    if not text: return []
    t = _norm(text)
    tokens = t.split()
    
    commands = []
    i = 0
    while i < len(tokens):
        best_match_len, best_canon = 0, None
        
        for phrase, canon in _NORM_PHRASES.items():
            ptoks = phrase.split()
            plen = len(ptoks)
            if i + plen <= len(tokens) and tokens[i:i+plen] == ptoks:
                if plen > best_match_len:
                    best_match_len, best_canon = plen, canon
        
        if best_canon:
            commands.append(best_canon)
            i += best_match_len
            continue
            
        
        word = tokens[i]
        if word in _NORM_PHRASES:
            commands.append(_NORM_PHRASES[word])
            i += 1
            continue
            
        
        
        best_sc, best_c, best_p = 0.0, None, ""
        
        for phrase, canon in _NORM_PHRASES.items():
            if len(phrase.split()) == 1:
                sc = _similar(word, phrase)
                if sc > best_sc:
                    best_sc, best_c, best_p = sc, canon, phrase
        
        if best_sc >= fuzzy_threshold:
            logger.debug(f"[VOICE] Fuzzy match: '{word}' ~ '{best_p}' ({best_sc*100:.0f}%) -> {best_c}")
            commands.append(best_c)
            
        i += 1
        
    return commands

def _normalize_state(value) -> bool:
    if isinstance(value, bool): return value
    if isinstance(value, (int, float)): return bool(int(value))
    if isinstance(value, str):
        v = value.strip().lower()
        if v in ("on","true","1"):  return True
        if v in ("off","false","0"): return False
    raise ValueError(f"Invalid state value: {value!r}")

def _ensure_dict(payload):
    if isinstance(payload, (list, tuple)) and len(payload) == 1:
        payload = payload[0]
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, (bytes, bytearray)):
        payload = payload.decode("utf-8", errors="strict")
    if isinstance(payload, str):
        s = payload.strip()
        try:
            return json.loads(s)
        except Exception:
            try:
                
                val = ast.literal_eval(s)
                if isinstance(val, (list, tuple)) and len(val) == 1 and isinstance(val[0], dict):
                    return val[0]
                if isinstance(val, dict):
                    return val
            except Exception:
                pass
        trunc_s = s if len(s) <= 80 else s[0:80] + "..."
        raise ValueError(f"Unsupported string payload: {trunc_s}")
    raise ValueError(f"Unsupported payload type: {type(payload).__name__}")
