# VERY UNSTABLE!!!
# HIGHLY EXPERIMENTAL
# NOT RECOMMENDED
# USE AT YOUR OWN RISK
"""
Merged converter.py for Skyrim Mod Translator

This file combines the translator logic along with all modules from the
plugin_interface package (plugin, plugin_string, utilities, datatypes, subrecord,
record, group, flags).

License: Attribution-NonCommercial-NoDerivatives 4.0 International (for plugin_interface code)
and other applicable licenses.
"""

###############################
# Begin plugin_interface code #
###############################

# ---------- plugin_string.py ----------
from dataclasses import dataclass
from enum import Enum, auto

@dataclass
class PluginString:
    """
    Class for translation strings.
    """
    editor_id: str | None
    """
    EditorIDs are the IDs that are visible in CK, xTranslator and xEdit,
    but not all strings have one.
    """
    form_id: str | None
    """
    FormIDs are hexadecimal numbers that identify the record of the string.
    """
    index: int | None
    """
    String index in current record (only for INFO and QUST).
    """
    type: str
    """
    Scheme: Record Subrecord, e.g. WEAP FULL.
    """
    original_string: str
    """
    String from original Plugin.
    """
    translated_string: str | None = None
    """
    Is None if string has no translation.
    """

    class Status(Enum):
        """
        Enum for string status.
        """
        NoTranslationRequired = auto()
        TranslationComplete = auto()
        TranslationIncomplete = auto()
        TranslationRequired = auto()

        @classmethod
        def get(cls, name: str, default=None, /):
            try:
                return cls[name]
            except KeyError:
                return default

        @classmethod
        def get_members(cls):
            return [
                cls.NoTranslationRequired,
                cls.TranslationComplete,
                cls.TranslationIncomplete,
                cls.TranslationRequired,
            ]

    status: Status = None
    """
    Status visible in Editor Tab.
    """
    tree_item = None
    """
    Tree Item in Editor Tab.
    """

    @classmethod
    def from_string_data(cls, string_data: dict[str, str]) -> "PluginString":
        if "original" in string_data:
            status = cls.Status.get(string_data.get("status"), cls.Status.TranslationComplete)
            editor_id = string_data["editor_id"]
            form_id = string_data.get("form_id")
            if editor_id and not form_id:
                if editor_id.startswith("[") and editor_id.endswith("]"):
                    form_id = editor_id
                    editor_id = None
            return PluginString(
                editor_id=editor_id,
                form_id=form_id,
                index=string_data.get("index"),
                type=string_data["type"],
                original_string=string_data["original"],
                translated_string=string_data["string"],
                status=status,
            )
        else:
            status = cls.Status.get(string_data.get("status"), cls.Status.TranslationRequired)
            editor_id = string_data["editor_id"]
            form_id = string_data.get("form_id")
            if editor_id and not form_id:
                if editor_id.startswith("[") and editor_id.endswith("]"):
                    form_id = editor_id
                    editor_id = None
            return PluginString(
                editor_id=editor_id,
                form_id=form_id,
                index=string_data.get("index"),
                type=string_data["type"],
                original_string=string_data["string"],
                status=status,
            )

    def to_string_data(self) -> dict[str, str]:
        if self.translated_string is not None:
            return {
                "editor_id": self.editor_id,
                "form_id": self.form_id,
                "index": self.index,
                "type": self.type,
                "original": self.original_string,
                "string": self.translated_string,
                "status": self.status.name,
            }
        else:
            return {
                "editor_id": self.editor_id,
                "form_id": self.form_id,
                "index": self.index,
                "type": self.type,
                "string": self.original_string,
                "status": self.status.name,
            }

    def __hash__(self):
        return hash((self.form_id.lower(), self.editor_id, self.index, self.type))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, PluginString):
            return hash(other) == hash(self)
        raise ValueError(f"Comparison between PluginString and object of type {type(other)} not possible!")

    def __getstate__(self):
        state = self.__dict__.copy()
        if self.tree_item:
            del state["tree_item"]
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.tree_item = None

# ---------- utilities.py ----------
from io import BufferedReader, BytesIO
from pathlib import Path
import jstyleson as json  # Ensure you have jstyleson installed

# Load file that defines which records contain subrecords that are strings
whitelist_path = Path("string_records.json").resolve()
with whitelist_path.open() as whitelist_file:
    STRING_RECORDS: dict[str, list[str]] = json.load(whitelist_file)

def peek(stream: BufferedReader, length: int):
    """
    Peeks into stream and returns data.
    """
    data = stream.read(length)
    stream.seek(-length, 1)
    return data

CHAR_WHITELIST = ["\n", "\r", "\t", "\u200B", "\xa0", "\u3000"]
STRING_BLACKLIST = ["<p>"]
STRING_WHITELIST = ["WoollyRhino", "CuSith"]

def get_checksum(number: int):
    """
    Returns horizontal checksum of `number` (sum of all digits).
    """
    return sum(int(digit) for digit in str(abs(number)))

def is_camel_case(text: str):
    """
    Checks if `text` is camel case without spaces.
    """
    if len(text) < 3:
        return False
    return (any(char.isupper() and char.isalpha() for char in text[2:]) and
            not text.isupper() and text.isalnum())

def is_snake_case(text: str):
    """
    Checks if `text` is snake case without spaces.
    """
    return " " not in text and "_" in text

def is_valid_string(text: str):
    """
    Checks if <text> is a valid string.
    """
    if not text.strip() or text in STRING_BLACKLIST:
        return False
    if text in STRING_WHITELIST or "<Alias" in text:
        return True
    if is_camel_case(text) or is_snake_case(text):
        return False
    return all(char.isprintable() or char in CHAR_WHITELIST for char in text)

def get_stream(data: BufferedReader | bytes) -> BytesIO:
    return BytesIO(data) if isinstance(data, bytes) else data

def read_data(data: BufferedReader | bytes, size: int) -> bytes:
    if isinstance(data, bytes):
        return data[:size]
    else:
        return data.read(size)

def indent_text(text: str, indent: int = 4):
    lines = [" " * indent + line for line in text.splitlines() if line.strip()]
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")

def prettyprint_object(obj: object):
    text = "\r{\n"
    text += f"    class = {type(obj).__name__}\n"
    for key, val in obj.__dict__.items():
        if isinstance(val, list):
            if not val:
                text += indent_text(f"{key}: list = []\n")
            else:
                text += indent_text(f"{key}: list = [\n")
                for item in val:
                    text += indent_text(prettyprint_object(item), 8) + ",\n"
                text += "    ]\n"
        elif isinstance(val, (str, bytes)):
            text += indent_text(f"{key}: {type(val).__name__} = {val[:20]!r}\n")
        else:
            text += indent_text(f"{key}: {type(val).__name__} = {val!r}\n")
    text += "}"
    return text

# ---------- datatypes.py ----------
import enum
import struct
from io import BufferedReader

class Integer:
    """
    Class for all types of signed and unsigned integers.
    """
    class IntType(enum.Enum):
        UInt8 = (1, False)
        UInt16 = (2, False)
        UInt32 = (4, False)
        UInt64 = (8, False)
        Int8 = (1, True)
        Int16 = (2, True)
        Int32 = (4, True)
        Int64 = (8, True)

    @staticmethod
    def parse(data: BufferedReader | bytes, typ: "Integer.IntType | tuple[int, bool]"):
        if isinstance(typ, Integer.IntType):
            size, signed = typ.value
        else:
            size, signed = typ
        return int.from_bytes(get_stream(data).read(size), byteorder="little", signed=signed)

    @staticmethod
    def dump(value: int, typ: "Integer.IntType | tuple[int, bool]"):
        if isinstance(typ, Integer.IntType):
            size, signed = typ.value
        else:
            size, signed = typ
        return value.to_bytes(size, byteorder="little", signed=signed)

class Float:
    """
    Class for all types of floats.
    """
    class FloatType(enum.Enum):
        Float32 = (4, "f")
        Float64 = (8, "d")
        Float = (4, "f")
        Double = (8, "d")

    @staticmethod
    def parse(data: BufferedReader | bytes, typ: "Float.FloatType") -> float:
        size, fmt = typ.value
        return struct.unpack(fmt, get_stream(data).read(size))[0]

    @staticmethod
    def dump(value: float, typ: "Float.FloatType"):
        size, fmt = typ.value
        return struct.pack(fmt, value)

class RawString(str):
    """
    Class for all types of chars and strings.
    """
    SUPPORTED_ENCODINGS = ["utf8", "cp1250", "cp1252", "cp1251"]

    class StrType(enum.Enum):
        Char = enum.auto()
        WChar = enum.auto()
        BZString = enum.auto()
        BString = enum.auto()
        WString = enum.auto()
        WZString = enum.auto()
        ZString = enum.auto()
        String = enum.auto()
        List = enum.auto()

    encoding: str

    @staticmethod
    def from_str(string: str, encoding: str):
        raw = RawString(string)
        raw.encoding = encoding
        return raw

    @staticmethod
    def decode(data: bytes):
        for encoding in RawString.SUPPORTED_ENCODINGS:
            try:
                s = RawString(data.decode(encoding))
                s.encoding = encoding
                return s
            except UnicodeDecodeError:
                pass
        s = RawString(data.decode("utf8", errors="replace"))
        s.encoding = "utf8"
        return s

    @staticmethod
    def encode(string: "RawString") -> bytes:
        for encoding in RawString.SUPPORTED_ENCODINGS:
            try:
                data = str(string).encode(encoding)
                string.encoding = encoding
                return data
            except UnicodeEncodeError:
                pass
        data = str(string).encode("utf8", errors="replace")
        string.encoding = "utf8"
        return data

    @staticmethod
    def parse(data: BufferedReader | bytes, typ: "RawString.StrType", size: int = None):
        stream = get_stream(data)
        match typ:
            case typ.Char:
                return read_data(stream, 1)
            case typ.WChar:
                return read_data(stream, 2)
            case typ.BZString | typ.BString:
                size = Integer.parse(stream, Integer.IntType.UInt8)
                d = read_data(stream, size).strip(b"\x00")
                return RawString.decode(d)
            case typ.WString | typ.WZString:
                size = Integer.parse(stream, Integer.IntType.Int16)
                d = read_data(stream, size).strip(b"\x00")
                return RawString.decode(d)
            case typ.ZString:
                d = b""
                while (char := stream.read(1)) != b"\x00" and char:
                    d += char
                return RawString.decode(d)
            case typ.String:
                d = read_data(stream, size)
                return RawString.decode(d)
            case typ.List:
                strings = []
                while len(strings) < size:
                    s = b""
                    while (char := stream.read(1)) != b"\x00" and char:
                        s += char
                    if s:
                        strings.append(RawString.decode(s))
                return strings

    @staticmethod
    def dump(value: "list[RawString] | RawString", typ: "RawString.StrType") -> bytes:
        match typ:
            case typ.Char | typ.WChar | typ.String:
                return RawString.encode(value)
            case typ.BString:
                text = RawString.encode(value)
                size = Integer.dump(len(text), Integer.IntType.UInt8)
                return size + text
            case typ.BZString:
                text = RawString.encode(value) + b"\x00"
                size = Integer.dump(len(text), Integer.IntType.UInt8)
                return size + text
            case typ.WString:
                text = RawString.encode(value)
                size = Integer.dump(len(text), Integer.IntType.UInt16)
                return size + text
            case typ.WZString:
                text = RawString.encode(value) + b"\x00"
                size = Integer.dump(len(text), Integer.IntType.UInt16)
                return size + text
            case typ.ZString:
                return RawString.encode(value) + b"\x00"
            case typ.List:
                data = b"\x00".join(RawString.encode(v) for v in value) + b"\x00"
                return data

class Flags(enum.IntFlag):
    """
    Class for all types of flags.
    """
    @classmethod
    def parse(cls, data: BufferedReader | bytes, typ: "Integer.IntType"):
        value = Integer.parse(data, typ)
        return cls(value)

    def dump(self, typ: "Integer.IntType"):
        return Integer.dump(self.value, typ)

class Hex:
    """
    Class for hexadecimal strings.
    """
    @staticmethod
    def parse(data: BufferedReader | bytes, typ: "Integer.IntType" = Integer.IntType.ULong):
        number = Integer.parse(data, typ)
        return hex(number).removeprefix("0x").upper().zfill(8)

    @staticmethod
    def dump(value: str, typ: "Integer.IntType" = Integer.IntType.ULong):
        number = int(value, 16)
        return Integer.dump(number, typ)

# ---------- flags.py ----------
class RecordFlags(Flags):
    Master = 0x1
    DeletedGroup = 0x10
    Deleted = 0x20
    Constant = HiddenFromLocalMap = 0x40
    Localized = 0x80
    MustUpdateAnims = Inaccessible = 0x100
    LightMaster = HiddenFromLocalMap2 = MotionBlurCastsShadows = 0x200
    PersistentReference = QuestItem = 0x400
    InitiallyDisabled = 0x800
    Ignored = 0x1000
    VisibleWhenDistant = 0x8000
    Dangerous = 0x20000
    Compressed = 0x40000
    CantWait = 0x80000
    IsMarker = 0x100000
    NoAIAcquire = 0x2000000
    NavMeshGenFilter = 0x4000000
    NavMeshGenBoundingBox = 0x8000000
    ReflectedByAutoWater = 0x10000000
    DontHavokSettle = 0x20000000
    NavMeshGenGround = NoRespawn = 0x40000000
    MultiBound = 0x80000000

# ---------- subrecord.py ----------
import logging
from io import BufferedReader, BytesIO

class Subrecord:
    """
    Contains parsed subrecord data.
    """
    type: str
    size: int
    data: bytes
    log = logging.getLogger("PluginParser.Subrecord")

    def __init__(self, type: str = None):
        self.type = type

    def __repr__(self) -> str:
        return prettyprint_object(self)

    def __str__(self):
        return str(self.__dict__)

    def __len__(self):
        return len(self.dump())

    def parse(self, stream: BufferedReader, header_flags: RecordFlags):
        self.type = stream.read(4).decode()
        self.size = Integer.parse(stream, Integer.IntType.UInt16)
        self.data = stream.read(self.size)

    def dump(self) -> bytes:
        self.size = len(self.data)
        data = b""
        data += self.type.encode()
        data += Integer.dump(self.size, Integer.IntType.UInt16)
        data += self.data
        return data

class HEDR(Subrecord):
    """
    HEDR subrecord.
    """
    version: float
    records_num: int
    next_object_id: str

    def parse(self, stream: BufferedReader, header_flags: RecordFlags):
        super().parse(stream, header_flags)
        stream = BytesIO(self.data)
        self.version = Float.parse(stream, Float.FloatType.Float32)
        self.records_num = Integer.parse(stream, Integer.IntType.UInt32)
        self.next_object_id = Hex.parse(stream)

    def dump(self) -> bytes:
        self.data = b""
        self.data += Float.dump(self.version, Float.FloatType.Float32)
        self.data += Integer.dump(self.records_num, Integer.IntType.UInt32)
        self.data += Hex.dump(self.next_object_id)
        return super().dump()

class EDID(Subrecord):
    """
    EDID subrecord.
    """
    editor_id: RawString

    def parse(self, stream: BufferedReader, header_flags: RecordFlags):
        super().parse(stream, header_flags)
        self.editor_id = RawString.parse(self.data, RawString.StrType.ZString)

    def dump(self) -> bytes:
        self.data = RawString.dump(self.editor_id, RawString.StrType.ZString)
        return super().dump()

class StringSubrecord(Subrecord):
    """
    String subrecord.
    """
    string: RawString | int
    index: int = 0
    log = logging.getLogger("PluginParser.StringSubrecord")

    def parse(self, stream: BufferedReader, header_flags: RecordFlags):
        super().parse(stream, header_flags)
        if RecordFlags.Localized in header_flags:
            self.string = Integer.parse(self.data, Integer.IntType.UInt32)
        else:
            self.string = RawString.parse(self.data, RawString.StrType.ZString, self.size)

    def set_string(self, string: str):
        encoding = self.string.encoding
        self.string = RawString.from_str(string, encoding)

    def dump(self) -> bytes:
        if isinstance(self.string, int):
            self.data = Integer.dump(self.string, Integer.IntType.UInt32)
        else:
            self.data = RawString.dump(self.string, RawString.StrType.ZString)
        return super().dump()

class MAST(Subrecord):
    """
    MAST subrecord.
    """
    file: str

    def parse(self, stream: BufferedReader, header_flags: RecordFlags):
        super().parse(stream, header_flags)
        self.file = RawString.parse(self.data, RawString.StrType.ZString)

    def dump(self) -> bytes:
        self.data = RawString.dump(self.file, RawString.StrType.ZString)
        return super().dump()

class XXXX(Subrecord):
    """
    Special XXXX subrecord.
    """
    field_size: int

    def parse(self, stream: BufferedReader, header_flags: RecordFlags):
        super().parse(stream, header_flags)
        self.field_size = Integer.parse(self.data, (self.size, False))
        self.data = stream.read(self.field_size + 7)

    def dump(self):
        data = b""
        data += self.type.encode()
        data += Integer.dump(self.size, Integer.IntType.UInt16)
        data += Integer.dump(self.field_size, (self.size, False))
        data += self.data
        return data

class TRDT(Subrecord):
    """
    TRDT subrecord.
    """
    emotion_type: int
    emotion_value: int
    unknown1: int
    response_id: int
    junk1: bytes
    sound_file: str
    use_emo_anim: int
    junk2: bytes

    def parse(self, stream: BufferedReader, header_flags: RecordFlags):
        super().parse(stream, header_flags)
        stream = BytesIO(self.data)
        self.emotion_type = Integer.parse(stream, Integer.IntType.UInt32)
        self.emotion_value = Integer.parse(stream, Integer.IntType.UInt32)
        self.unknown1 = Integer.parse(stream, Integer.IntType.Int32)
        self.response_id = Integer.parse(stream, Integer.IntType.UInt8)
        self.junk1 = stream.read(3)
        self.sound_file = Hex.parse(stream)
        self.use_emo_anim = Integer.parse(stream, Integer.IntType.UInt8)
        self.junk2 = stream.read(3)

    def dump(self):
        self.data = b""
        self.data += Integer.dump(self.emotion_type, Integer.IntType.UInt32)
        self.data += Integer.dump(self.emotion_value, Integer.IntType.UInt32)
        self.data += Integer.dump(self.unknown1, Integer.IntType.Int32)
        self.data += Integer.dump(self.response_id, Integer.IntType.UInt8)
        self.data += self.junk1
        self.data += Hex.dump(self.sound_file)
        self.data += Integer.dump(self.use_emo_anim, Integer.IntType.UInt8)
        self.data += self.junk2
        return super().dump()

class QOBJ(Subrecord):
    """
    QOBJ subrecord.
    """
    index: int

    def parse(self, stream: BufferedReader, header_flags: RecordFlags):
        super().parse(stream, header_flags)
        self.index = Integer.parse(self.data, Integer.IntType.Int16)

    def dump(self):
        self.data = Integer.dump(self.index, Integer.IntType.Int16)
        return super().dump()

class EPFT(Subrecord):
    """
    EPFT subrecord.
    """
    perk_type: int

    def parse(self, stream: BufferedReader, header_flags: RecordFlags):
        super().parse(stream, header_flags)
        self.perk_type = Integer.parse(self.data, Integer.IntType.UInt8)

    def dump(self):
        self.data = Integer.dump(self.perk_type, Integer.IntType.UInt8)
        return super().dump()

SUBRECORD_MAP: dict[str, type[Subrecord]] = {
    "HEDR": HEDR,
    "EDID": EDID,
    "MAST": MAST,
    "TRDT": TRDT,
    "QOBJ": QOBJ,
    "EPFT": EPFT,
    "XXXX": XXXX,
}

# ---------- record.py ----------
import zlib
from io import BufferedReader, BytesIO

class Record:
    """
    Contains parsed record data.
    """
    type: str
    size: int
    flags: RecordFlags
    formid: str
    timestamp: int
    version_control_info: int
    internal_version: int
    unknown: int
    data: bytes
    subrecords: list[Subrecord]
    log = logging.getLogger("PluginParser")

    def __repr__(self) -> str:
        return prettyprint_object(self)

    def __len__(self):
        return len(self.dump())

    def parse(self, stream: BufferedReader, header_flags: RecordFlags):
        self.type = stream.read(4).decode()
        self.size = Integer.parse(stream, Integer.IntType.UInt32)
        self.flags = RecordFlags.parse(stream, Integer.IntType.UInt32)
        self.formid = Hex.parse(stream)
        self.timestamp = Integer.parse(stream, Integer.IntType.UInt16)
        self.version_control_info = Integer.parse(stream, Integer.IntType.UInt16)
        self.internal_version = Integer.parse(stream, Integer.IntType.UInt16)
        self.unknown = Integer.parse(stream, Integer.IntType.UInt16)
        if RecordFlags.Compressed in self.flags:
            decompressed_size = Integer.parse(stream, Integer.IntType.UInt32)
            self.data = zlib.decompress(stream.read(self.size - 4))
            self.size = decompressed_size
        else:
            self.data = stream.read(self.size)
        match self.type:
            case "INFO":
                self.parse_info_record(header_flags)
            case "PERK":
                self.parse_perk_record(header_flags)
            case "QUST":
                self.parse_qust_record(header_flags)
            case _:
                self.parse_subrecords(header_flags)

    def parse_qust_record(self, header_flags: RecordFlags):
        stream = BytesIO(self.data)
        self.subrecords = []
        def calc_condition_index(stage_index: int) -> int:
            ctda_subrecords: list[Subrecord] = []
            for subrecord in self.subrecords[::-1]:
                if subrecord.type == "CTDA":
                    ctda_subrecords.append(subrecord)
                else:
                    break
            hashes = [abs(hash(subrecord.data)) for subrecord in ctda_subrecords[::-1]]
            index = get_checksum(sum(hashes) - stage_index)
            return index
        current_stage_index = 0
        current_objective_index = 0
        while stream.tell() < len(self.data):
            subrecord_type = peek(stream, 4).decode()
            if subrecord_type in STRING_RECORDS.get(self.type, []):
                subrecord = StringSubrecord(subrecord_type)
            else:
                subrecord = SUBRECORD_MAP.get(subrecord_type, Subrecord)()
            subrecord.parse(stream, header_flags)
            match subrecord_type:
                case "INDX":
                    current_stage_index = abs(hash(subrecord.data))
                case "CNAM":
                    subrecord.index = calc_condition_index(current_stage_index)
                case "QOBJ":
                    current_objective_index = subrecord.index
                case "NNAM":
                    subrecord.index = current_objective_index
            self.subrecords.append(subrecord)

    def parse_info_record(self, header_flags: RecordFlags):
        stream = BytesIO(self.data)
        self.subrecords = []
        current_index = 0
        while stream.tell() < len(self.data):
            subrecord_type = peek(stream, 4).decode()
            if subrecord_type in STRING_RECORDS.get(self.type, []):
                subrecord = StringSubrecord(subrecord_type)
            else:
                subrecord = SUBRECORD_MAP.get(subrecord_type, Subrecord)()
            subrecord.parse(stream, header_flags)
            match subrecord_type:
                case "TRDT":
                    current_index = subrecord.response_id
                case "NAM1":
                    subrecord.index = current_index
            self.subrecords.append(subrecord)

    def parse_perk_record(self, header_flags: RecordFlags):
        stream = BytesIO(self.data)
        self.subrecords = []
        perk_type = None
        epfd_index = 0
        while stream.tell() < len(self.data):
            subrecord_type = peek(stream, 4).decode()
            if (perk_type == 4 and subrecord_type == "EPF2") or (perk_type == 7 and subrecord_type == "EPFD"):
                subrecord = StringSubrecord(subrecord_type)
            else:
                subrecord = SUBRECORD_MAP.get(subrecord_type, Subrecord)()
            subrecord.parse(stream, header_flags)
            self.subrecords.append(subrecord)
            match subrecord_type:
                case "EPFT":
                    perk_type = subrecord.perk_type
                case "EPFD":
                    subrecord.index = epfd_index
                    epfd_index += 1
                case "EPF2":
                    if peek(stream, 4) == b"EPF3":
                        index_subrecord = Subrecord()
                        index_subrecord.parse(stream, header_flags)
                        epf2_index = int.from_bytes(index_subrecord.data[2:], byteorder="little")
                        subrecord.index = epf2_index
                        self.subrecords.append(index_subrecord)
                    else:
                        self.log.warning(f"EPF2 Subrecord without following EPF3! Record: {self}")
    def parse_subrecords(self, header_flags: RecordFlags):
        stream = BytesIO(self.data)
        self.subrecords = []
        itxt_index = 0
        while stream.tell() < len(self.data):
            subrecord_type = peek(stream, 4).decode()
            if subrecord_type in STRING_RECORDS.get(self.type, []):
                subrecord = StringSubrecord(subrecord_type)
            else:
                subrecord = SUBRECORD_MAP.get(subrecord_type, Subrecord)()
            subrecord.parse(stream, header_flags)
            if subrecord.type == "ITXT":
                subrecord.index = itxt_index
                itxt_index += 1
            self.subrecords.append(subrecord)

    def dump(self) -> bytes:
        data = b"".join(subrecord.dump() for subrecord in self.subrecords)
        if RecordFlags.Compressed in self.flags:
            uncompressed_size = Integer.dump(len(data), Integer.IntType.UInt32)
            data = uncompressed_size + zlib.compress(data)
        self.size = len(data)
        self.data = b""
        self.data += self.type.encode()
        self.data += Integer.dump(self.size, Integer.IntType.UInt32)
        self.data += RecordFlags.dump(self.flags, Integer.IntType.UInt32)
        self.data += Hex.dump(self.formid)
        self.data += Integer.dump(self.timestamp, Integer.IntType.UInt16)
        self.data += Integer.dump(self.version_control_info, Integer.IntType.UInt16)
        self.data += Integer.dump(self.internal_version, Integer.IntType.UInt16)
        self.data += Integer.dump(self.unknown, Integer.IntType.UInt16)
        self.data += data
        return self.data

# ---------- group.py ----------
from enum import IntEnum
from io import BytesIO

class Group:
    """
    GRUP record.
    """
    type: str
    group_size: int
    label: bytes | str | int
    group_type: int
    timestamp: int
    version_control_info: int
    unknown: int
    data: bytes
    children: list

    class GroupType(IntEnum):
        Normal = 0
        WorldChildren = 1
        InteriorCellBlock = 2
        InteriorCellSubBlock = 3
        ExteriorCellBlock = 4
        ExteriorCellSubBlock = 5
        CellChildren = 6
        TopicChildren = 7
        CellPersistentChildren = 8
        CellTemporaryChildren = 9

    def __repr__(self) -> str:
        return prettyprint_object(self)

    def __len__(self):
        return len(self.dump())

    def parse(self, stream: BufferedReader, header_flags: Flags):
        self.type = stream.read(4).decode()
        self.group_size = Integer.parse(stream, Integer.IntType.UInt32)
        label = stream.read(4)
        self.group_type = Integer.parse(stream, Integer.IntType.Int32)
        self.timestamp = Integer.parse(stream, Integer.IntType.UInt16)
        self.version_control_info = Integer.parse(stream, Integer.IntType.UInt16)
        self.unknown = Integer.parse(stream, Integer.IntType.UInt32)
        self.data = stream.read(self.group_size - 24)
        record_stream = BytesIO(self.data)
        match self.group_type:
            case Group.GroupType.Normal:
                self.label = label.decode()
                self.parse_records(record_stream, header_flags)
            case Group.GroupType.TopicChildren:
                self.label = Hex.parse(label)
                self.parse_records(record_stream, header_flags)
            case Group.GroupType.WorldChildren:
                self.label = Hex.parse(label)
                self.parse_records(record_stream, header_flags)
            case Group.GroupType.ExteriorCellBlock:
                label_stream = BytesIO(label)
                self.grid = (Integer.parse(label_stream, Integer.IntType.Int16),
                             Integer.parse(label_stream, Integer.IntType.Int16))
                self.parse_records(record_stream, header_flags)
            case Group.GroupType.ExteriorCellSubBlock:
                label_stream = BytesIO(label)
                self.grid = (Integer.parse(label_stream, Integer.IntType.Int16),
                             Integer.parse(label_stream, Integer.IntType.Int16))
                self.parse_records(record_stream, header_flags)
            case Group.GroupType.InteriorCellBlock:
                self.block_number = Integer.parse(label, Integer.IntType.Int32)
                self.parse_records(record_stream, header_flags)
            case Group.GroupType.InteriorCellSubBlock:
                self.subblock_number = Integer.parse(label, Integer.IntType.Int32)
                self.parse_records(record_stream, header_flags)
            case Group.GroupType.CellChildren | Group.GroupType.CellPersistentChildren | Group.GroupType.CellTemporaryChildren:
                self.parent_cell = Hex.parse(label)
                self.parse_records(record_stream, header_flags)
            case _:
                raise Exception(f"Unknown Group Type: {self.group_type}")

    def parse_records(self, stream: BytesIO, header_flags: Flags):
        self.children = []
        while child_type := peek(stream, 4):
            child_type = child_type.decode()
            if child_type == "GRUP":
                child = Group()
            else:
                child = Record()
            child.parse(stream, header_flags)
            self.children.append(child)

    def dump(self) -> bytes:
        child_data = b"".join(child.dump() for child in self.children)
        self.group_size = len(child_data) + 24
        data = b""
        data += self.type.encode()
        data += Integer.dump(self.group_size, Integer.IntType.UInt32)
        match self.group_type:
            case Group.GroupType.Normal:
                data += self.label.encode()
            case Group.GroupType.WorldChildren | Group.GroupType.TopicChildren:
                data += Hex.dump(self.label)
            case Group.GroupType.CellChildren | Group.GroupType.CellPersistentChildren | Group.GroupType.CellTemporaryChildren:
                data += Hex.dump(self.parent_cell)
            case Group.GroupType.ExteriorCellBlock | Group.GroupType.ExteriorCellSubBlock:
                data += Integer.dump(self.grid[0], Integer.IntType.Int16)
                data += Integer.dump(self.grid[1], Integer.IntType.Int16)
            case Group.GroupType.InteriorCellBlock:
                data += Integer.dump(self.block_number, Integer.IntType.Int32)
            case Group.GroupType.InteriorCellSubBlock:
                data += Integer.dump(self.subblock_number, Integer.IntType.Int32)
        data += Integer.dump(self.group_type, Integer.IntType.Int32)
        data += Integer.dump(self.timestamp, Integer.IntType.UInt16)
        data += Integer.dump(self.version_control_info, Integer.IntType.UInt16)
        data += Integer.dump(self.unknown, Integer.IntType.UInt32)
        data += child_data
        return data

# ---------- plugin.py ----------
from io import BufferedReader
from pathlib import Path

class Plugin:
    """
    Contains parsed plugin data.
    """
    path: Path
    header: Record
    groups: list[Group]
    __string_subrecords: dict[PluginString, StringSubrecord] = None
    log = logging.getLogger("PluginInterface")

    def __init__(self, path: Path):
        self.path = path
        self.load()

    def __repr__(self) -> str:
        return prettyprint_object(self)

    def __len__(self):
        return len(self.dump())

    def __str__(self) -> str:
        return self.__repr__()

    def load(self):
        with self.path.open("rb") as stream:
            self.parse(stream)

    def parse(self, stream: BufferedReader):
        self.log.info(f"Parsing {str(self.path)!r}...")
        self.groups = []
        self.header = Record()
        self.header.parse(stream, [])
        while peek(stream, 1):
            group = Group()
            group.parse(stream, self.header.flags)
            self.groups.append(group)
        self.log.info("Parsing complete.")

    def dump(self):
        data = self.header.dump()
        for group in self.groups:
            data += group.dump()
        return data

    @staticmethod
    def get_record_edid(record: Record):
        try:
            for subrecord in record.subrecords:
                if isinstance(subrecord, EDID):
                    return subrecord.editor_id
        except AttributeError:
            return None

    def extract_group_strings(self, group: Group, extract_localized: bool = False, unfiltered: bool = False):
        strings: dict[PluginString, StringSubrecord] = {}
        masters = [subrecord.file for subrecord in self.header.subrecords if isinstance(subrecord, MAST)]
        for record in group.children:
            if isinstance(record, Group):
                strings |= self.extract_group_strings(record, extract_localized)
            else:
                edid = self.get_record_edid(record)
                master_index = int(record.formid[:2], 16)
                try:
                    master = masters[master_index]
                except IndexError:
                    master = self.path.name
                formid = f"{record.formid}|{master}"
                if (self.path.suffix.lower() == ".esl" or RecordFlags.LightMaster in self.header.flags) and master == self.path.name:
                    formid = "FE" + formid[2:]
                for subrecord in record.subrecords:
                    if isinstance(subrecord, StringSubrecord):
                        string_value = subrecord.string
                        if (isinstance(string_value, RawString) or extract_localized) and (is_valid_string(string_value) or unfiltered):
                            string_data = PluginString(
                                editor_id=edid,
                                form_id=formid,
                                index=subrecord.index,
                                type=f"{record.type} {subrecord.type}",
                                original_string=str(string_value),
                                status=(PluginString.Status.TranslationRequired if is_valid_string(string_value) else PluginString.Status.NoTranslationRequired),
                            )
                            strings[string_data] = subrecord
        return strings

    def extract_strings(self, extract_localized: bool = False, unfiltered: bool = False):
        strings: list[PluginString] = []
        for group in self.groups:
            current_group = list(self.extract_group_strings(group, extract_localized, unfiltered).keys())
            strings += current_group
        return strings

    def find_string_subrecord(self, form_id: str, typ: str, string: str, index: int | None) -> StringSubrecord | None:
        if self.__string_subrecords is None:
            string_subrecords: dict[PluginString, StringSubrecord] = {}
            for group in self.groups:
                current_group = self.extract_group_strings(group)
                string_subrecords |= current_group
            self.__string_subrecords = string_subrecords
        for plugin_string, subrecord in self.__string_subrecords.items():
            if (plugin_string.form_id[2:] == form_id[2:] and plugin_string.type == typ and 
                plugin_string.original_string == string and plugin_string.index == index):
                return subrecord

    def replace_strings(self, strings: list[PluginString]):
        for s in strings:
            subrecord = self.find_string_subrecord(s.form_id, s.type, s.original_string, s.index)
            if subrecord:
                subrecord.set_string(s.translated_string)
            else:
                self.log.error(f"Failed to replace string {s}: Subrecord not found!")

    @staticmethod
    def is_light(plugin_path: Path):
        if plugin_path.suffix.lower() == ".esl":
            return True
        with plugin_path.open("rb") as stream:
            header = Record()
            header.parse(stream, [])
        return RecordFlags.LightMaster in header.flags

###############################
# End plugin_interface code   #
###############################

####################################
# Begin Converter & Async Translate #
####################################

import json
import logging
import sys
import os
import time
import re
import asyncio
from pathlib import Path
from copy import copy

import openai
import ahocorasick

# --- SUPPRESS OPENAI/urllib3 LOGS ---
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Attempt to import tiktoken for token counting; fallback to simple split.
try:
    import tiktoken
    tokenizer = tiktoken.encoding_for_model("gpt-4o-mini")
except Exception:
    tokenizer = None

def count_tokens(text: str) -> int:
    if tokenizer is not None:
        return len(tokenizer.encode(text))
    else:
        return len(text.split())

# Setup minimal logger.
log_fmt = "[%(asctime)s.%(msecs)03d][%(levelname)s]: %(message)s"
root_logger = logging.getLogger()
root_logger.setLevel("INFO")
formatter = logging.Formatter(log_fmt, datefmt="%d.%m.%Y %H:%M:%S")
log_handler = logging.StreamHandler(sys.stdout)
log_handler.setFormatter(formatter)
root_logger.addHandler(log_handler)
log = logging.getLogger("Converter")

openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    log.error("OPENAI_API_KEY environment variable is not set.")
    sys.exit(1)

def load_term_mapping(mods_root: Path) -> dict[str, str]:
    mapping = {}
    mapping_file = mods_root / "all.txt"
    if not mapping_file.exists():
        log.warning(f"No all.txt found in {mods_root}. No basic term replacements will be applied.")
        return mapping
    with mapping_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.rsplit(maxsplit=1)
            if len(parts) < 2:
                continue
            mapping[parts[0].strip()] = parts[1].strip()
    log.info(f"Loaded {len(mapping)} term translations from {mapping_file}.")
    return mapping

def build_automaton(mapping: dict[str, str]) -> ahocorasick.Automaton:
    automaton = ahocorasick.Automaton()
    for eng, chi in mapping.items():
        automaton.add_word(eng.lower(), (eng, chi))
    automaton.make_automaton()
    return automaton

def apply_term_replacements(text: str, automaton: ahocorasick.Automaton) -> str:
    lower_text = text.lower()
    matches = []
    for end_index, (orig_key, chi) in automaton.iter(lower_text):
        start_index = end_index - len(orig_key) + 1
        if (start_index == 0 or not lower_text[start_index - 1].isalnum()) and \
           (end_index + 1 == len(lower_text) or not lower_text[end_index + 1].isalnum()):
            matches.append((start_index, end_index + 1, orig_key, chi))
    matches.sort(key=lambda x: (x[0], -(x[1] - x[0])))
    selected = []
    last_end = 0
    for start, end, orig_key, chi in matches:
        if start >= last_end:
            selected.append((start, end, orig_key, chi))
            last_end = end
    result = []
    last_index = 0
    for start, end, orig_key, chi in selected:
        result.append(text[last_index:start])
        result.append(chi)
        last_index = end
    result.append(text[last_index:])
    return "".join(result)

# --- LOG BUFFER CHANGES ---
LOG_BUFFER = []
LOG_BUFFER_SIZE = 5
LOG_LOCK = asyncio.Lock()

async def buffer_log_message(batch_index, attempt, duration, input_tokens, output_tokens, cost):
    async with LOG_LOCK:
        LOG_BUFFER.append((batch_index, attempt, duration, input_tokens, output_tokens, cost))
        if len(LOG_BUFFER) == LOG_BUFFER_SIZE:
            first_attempt = LOG_BUFFER[0][1]
            first_duration = LOG_BUFFER[0][2]
            first_input_tokens = LOG_BUFFER[0][3]
            first_output_tokens = LOG_BUFFER[0][4]
            first_cost = LOG_BUFFER[0][5]
            batch_ids = [str(item[0]) for item in LOG_BUFFER]
            combined_ids = ", ".join(batch_ids)
            log.info(
                f"Batch {combined_ids} attempt {first_attempt}: API call took {first_duration:.2f}s, "
                f"input tokens: {first_input_tokens}, output tokens: {first_output_tokens}, "
                f"cost: ${first_cost:.6f}"
            )
            LOG_BUFFER.clear()

async def async_translate_chunk(batch_index: int, chunk: list[str], max_retries: int = 3, delay: float = 1.0) -> tuple[int, list[str]]:
    for attempt in range(1, max_retries + 1):
        lines_prompt = "\n".join(f"{i + 1}. {txt}" for i, txt in enumerate(chunk))
        user_content = (
            "You are a professional translator specialized in Traditional Chinese. "
            "Translate the following numbered lines from English to Traditional Chinese. "
            "Output ONLY a valid JSON array of strings with the translations corresponding to each input line in order. "
            "Do not include any additional text, code fences, or formatting. "
            f"The input contains {len(chunk)} lines:\n{lines_prompt}\n"
            "Provide your answer as a JSON array exactly in this format:\n"
            "[\"translation for line 1\", \"translation for line 2\", ...]"
        )
        input_tokens = count_tokens(user_content)
        try:
            start_api = time.perf_counter()
            response = await openai.ChatCompletion.acreate(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful translation assistant."},
                    {"role": "user", "content": user_content},
                ],
                temperature=0,
            )
            end_api = time.perf_counter()
            duration = end_api - start_api
            response_text = response["choices"][0]["message"]["content"].strip()
            output_tokens = count_tokens(response_text)
            cost = (input_tokens / 1_000_000 * 0.15) + (output_tokens / 1_000_000 * 0.6)
            await buffer_log_message(batch_index, attempt, duration, input_tokens, output_tokens, cost)
            if not response_text:
                raise ValueError("Empty response text")
            translations = json.loads(response_text)
            if not isinstance(translations, list) or len(translations) != len(chunk):
                log.warning(f"Batch {batch_index} attempt {attempt}: Expected {len(chunk)} translations, got {len(translations) if isinstance(translations, list) else 'invalid output'}. Retrying...")
                await asyncio.sleep(delay)
                continue
            return batch_index, translations
        except Exception as e:
            log.error(f"Batch {batch_index} attempt {attempt}: Error during translation: {e}")
            await asyncio.sleep(delay)
    log.error(f"Batch {batch_index}: Failed after {max_retries} attempts. Using original texts as fallback.")
    return batch_index, chunk

async def async_translate_in_batches(strings_to_translate: list[str], batch_size: int = 10, max_workers: int = 64) -> list[str]:
    batches = [(i, strings_to_translate[i : i + batch_size]) for i in range(0, len(strings_to_translate), batch_size)]
    log.info(f"Total async batches to process: {len(batches)}")
    tasks = [async_translate_chunk(batch_index, chunk) for batch_index, chunk in batches]
    results = await asyncio.gather(*tasks)
    results.sort(key=lambda x: x[0])
    final_translations = []
    for _, translations in results:
        final_translations.extend(translations)
    return final_translations

async def async_process_plugin_file(plugin_path: Path, output_path: Path, term_automaton: ahocorasick.Automaton) -> None:
    file_start = time.perf_counter()
    log.info(f"Processing {plugin_path}...")
    try:
        plugin = Plugin(plugin_path)
    except Exception as e:
        log.error(f"Error loading plugin {plugin_path}: {e}")
        return
    try:
        extracted_strings = plugin.extract_strings()
    except Exception as e:
        log.error(f"Error extracting strings from {plugin_path}: {e}")
        return
    if not extracted_strings:
        log.info(f"No strings found in {plugin_path}. Skipping.")
        return
    log.info(f"Extracted {len(extracted_strings)} strings from {plugin_path}.")
    texts_to_translate = []
    for s in extracted_strings:
        text = (s.translated_string if s.translated_string else s.original_string) or ""
        text = apply_term_replacements(text, term_automaton)
        texts_to_translate.append(text)
    log.info("Starting async batch translation...")
    translations = await async_translate_in_batches(texts_to_translate, batch_size=10, max_workers=64)
    processed_strings = []
    for s, translated_text in zip(extracted_strings, translations):
        new_s = copy(s)
        translated_text = translated_text.replace("Knows", "知曉")
        translated_text = re.sub(r"\s+", "", translated_text)
        new_s.translated_string = translated_text
        new_s.status = new_s.Status.TranslationComplete
        processed_strings.append(new_s)
    string_data = [s.to_string_data() for s in processed_strings]
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf8") as f:
            json.dump(string_data, f, ensure_ascii=False, indent=4)
        log.info(f"Written {len(processed_strings)} string(s) to {output_path}")
    except Exception as e:
        log.error(f"Error writing to {output_path}: {e}")
    file_end = time.perf_counter()
    log.info(f"Processing of {plugin_path} completed in {file_end - file_start:.2f} seconds.")

async def async_main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python converter.py <path_to_mods_directory>")
        sys.exit(1)
    mods_root = Path(sys.argv[1])
    if not mods_root.is_dir():
        log.error(f"Provided path {mods_root!r} is not a valid directory.")
        sys.exit(1)
    term_mapping = load_term_mapping(mods_root)
    term_automaton = build_automaton(term_mapping)
    output_root = Path("Output")
    esp_files = []
    for subfolder in mods_root.iterdir():
        if subfolder.is_dir():
            esp_files.extend(list(subfolder.glob("*.esp")))
    if not esp_files:
        log.warning("No .esp files found in the immediate subfolders of the provided directory.")
        sys.exit(0)
    total_start = time.perf_counter()
    tasks = []
    for esp_file in esp_files:
        relative_path = esp_file.relative_to(mods_root)
        output_file = output_root / relative_path.parent / f"{esp_file.stem}_output{esp_file.suffix}.json"
        tasks.append(async_process_plugin_file(esp_file, output_file, term_automaton))
    await asyncio.gather(*tasks)
    total_end = time.perf_counter()
    log.info(f"Total processing time for all files: {total_end - total_start:.2f} seconds.")

if __name__ == "__main__":
    asyncio.run(async_main())
