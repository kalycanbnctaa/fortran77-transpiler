# Fortran77 to C Transpiler

Transpiler dari subset **Fortran 77** (fixed-form) ke **C**, dikerjakan sebagai Task Seleksi Lab IRK 2026.

Program mengimplementasikan pipeline kompiler lengkap: **Lexer → Parser/AST → Analisis Semantik → Code Generation**, dengan opsi untuk menampilkan keluaran tiap tahap secara terpisah.

## Author
| NIM | Nama |
|---|---|
| 13524071 | Kalyca Nathania Benedicta Manullang|

---

## Daftar Isi

- [Requirements](#requirements)
- [Instalasi](#instalasi)
- [Cara Menjalankan](#cara-menjalankan)
- [Struktur Proyek](#struktur-proyek)
- [Arsitektur Pipeline](#arsitektur-pipeline)
- [Detail Desain](#detail-desain)
  - [1. Fixed-Form Processor](#1-fixed-form-processor)
  - [2. Lexer](#2-lexer)
  - [3. Parser dan AST](#3-parser--ast)
  - [4. Analisis Semantik](#4-analisis-semantik)
  - [5. Code Generation](#5-code-generation)
- [Padanan Konstruksi Fortran 77 ⟺ C](#padanan-konstruksi-fortran-77--c)
- [Precedence Operator](#precedence-operator)
- [Fitur Bonus](#fitur-bonus)
- [Pengujian](#pengujian)
- [Cakupan dan Batasan](#cakupan--batasan)
- [Referensi](#referensi)

---

## Requirements

- Python 3.13+
- `gcc` (untuk mengompilasi hasil `.c` yang di-generate)
- `gfortran` (opsional, hanya dibutuhkan untuk menjalankan test suite yang membandingkan output dengan program Fortran asli)

## Instalasi

```bash
python -m venv .venv
```

Aktifkan virtual environment.

Windows:

```bash
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Install dependency:

```bash
pip install -r requirements.txt
```

Untuk menjalankan test suite, install juga dependency development:

```bash
pip install -r requirements-dev.txt
```

## Cara Menjalankan

### Menjalankan pipeline lengkap (langsung menghasilkan kode C)

```bash
python main.py examples/hello.f
```

Menyimpan hasil ke file `.c`:

```bash
python main.py examples/hello.f -o output.c
```

### Menampilkan keluaran tiap tahap komponen secara terpisah

Sesuai requirement spesifikasi, setiap tahap pipeline bisa ditampilkan sendiri-sendiri:

Menampilkan hasil lexer (token stream):

```bash
python main.py examples/hello.f --tokens
```

Menampilkan Abstract Syntax Tree (AST):

```bash
python main.py examples/hello.f --ast
```

Menampilkan symbol table hasil analisis semantik:

```bash
python main.py examples/hello.f --symbols
```

Meng-generate kode C secara eksplisit:

```bash
python main.py examples/hello.f --emit
```

Meng-generate kode C dengan source map (komentar `// line N`, lihat [Fitur Bonus](#fitur-bonus)):

```bash
python main.py examples/hello.f --emit --source-map
```

Semua flag di atas bisa dikombinasikan dalam satu perintah, misalnya untuk melihat token, AST, dan symbol table sekaligus:

```bash
python main.py examples/hello.f --tokens --ast --symbols
```

### Mengompilasi dan menjalankan hasil `.c`

```bash
python main.py examples/hello.f -o output.c
gcc output.c -o output -lm
./output
```

Flag `-lm` diperlukan karena kode C yang di-generate menyertakan `<math.h>` untuk fungsi intrinsik seperti `SQRT`, `SIN`, `ABS`, dsb.

### Bantuan

```bash
python main.py --help
```

---

## Struktur Proyek

```
fortran77-transpiler/
├── main.py                    # Entry point CLI
├── requirements.txt
├── requirements-dev.txt
│
├── src/
│   ├── lexer/                 # Fixed-form processor, scanner, tokenizer
│   ├── ast/                   # Definisi node AST + Visitor pattern
│   ├── parser/                # Recursive descent parser
│   ├── semantic/               # Symbol table, type checker, common/array checker
│   ├── codegen/                # Code generator ke C
│   └── visualization/          # Pretty-printer untuk token/AST/symbol table
│
├── examples/                  # Contoh program Fortran 77 untuk pengujian
│   ├── hello.f
│   ├── basic/
│   ├── arrays/
│   ├── common/
│   └── subprograms/
│
└── tests/
    ├── lexer/
    ├── parser/
    ├── semantic/
    ├── codegen/
    ├── integration/            # End-to-end: gfortran vs gcc, bandingkan output
    └── bonus/                  # CHARACTER, computed GOTO, source map
```

---

## Arsitektur Pipeline

```mermaid
flowchart TD
    A[Source Fortran (.f)] --> B[Fixed-Form Processor]
    
    B --> C[Lexer]
    
    C --> D[Parser<br>Recursive Descent]
    
    D --> E[Semantic Analyzer]
    
    E --> F[Code Generator]
    
    F --> G[Output C (.c)]
    
    B -->|NormalizedLine<br><i>label, statement, source_line</i>| C
    C -->|Token stream<br><i>keyword, identifier, literal, operator</i>| D
    D -->|TranslationUnit<br><i>AST</i>| E
    E -->|AST + SymbolTable<br><i>AST terdekorasi</i>| F
```

Setiap tahap dapat diakses secara independen lewat CLI flag (`--tokens`, `--ast`, `--symbols`, `--emit`), sesuai requirement untuk menunjukkan keluaran intermediate tiap komponen.

---

## Detail Desain

### 1. Fixed-Form Processor

**Lokasi:** `src/lexer/fixed_form.py`

Menangani format kolom kaku khas Fortran 77:

| Kolom | Fungsi |
|---|---|
| 1 | `C` atau `*` menandakan baris komentar (diabaikan seluruhnya) |
| 1–5 | Label baris (rapat kanan, harus numerik) |
| 6 | Continuation marker: karakter apa pun selain spasi/`0` berarti baris ini sambungan dari baris sebelumnya |
| 7–72 | Kode aktif |
| 73+ | Diabaikan (sequence number kartu punch era lama) |

Baris continuation digabung ke statement sebelumnya sebelum masuk ke tahap lexing, sehingga lexer selalu bekerja pada satu statement logis yang utuh. Ini penting karena sebuah ekspresi bisa terpecah jadi beberapa baris fisik:

```fortran
      TOTAL = 1 +
     +        2 +
     +        3
```

digabung menjadi satu statement logis: `TOTAL = 1 + 2 + 3`.

### 2. Lexer

**Lokasi:** `src/lexer/lexer.py`, `keywords.py`, `operators.py`, `token_type.py`

Lexer bekerja per-statement (bukan per-karakter mentah dari file), menghasilkan token untuk:

- **Keyword**: `PROGRAM`, `SUBROUTINE`, `FUNCTION`, `IF`, `DO`, `COMMON`, dst (case-insensitive, semua dinormalisasi ke uppercase)
- **Literal**: `INT_LITERAL`, `REAL_LITERAL` (termasuk notasi `.5`, `1.0E5`, `.5E2`), `CHARACTER_LITERAL` (diapit `'...'`), `TRUE`/`FALSE`
- **Operator titik**: `.AND.`, `.OR.`, `.NOT.`, `.EQ.`, `.NE.`, `.LT.`, `.LE.`, `.GT.`, `.GE.`
- **Operator simbol**: `+ - * / ** =` serta delimiter `( ) ,`
- **LABEL**: diemit terpisah di awal statement jika baris tersebut berlabel

### 3. Parser dan AST

**Lokasi:** `src/parser/` (recursive descent, ditulis manual sesuai rekomendasi spesifikasi), `src/ast/`

Parser dipecah menjadi beberapa mixin untuk keterbacaan:

- `SubprogramParserMixin`: `PROGRAM`, `SUBROUTINE`, `FUNCTION`
- `DeclarationParserMixin`: `IMPLICIT NONE`, deklarasi tipe, `COMMON`
- `StatementParserMixin`: assignment, `IF/THEN/ELSE/ENDIF`, `DO`, `GOTO`, `CALL`, `PRINT`, `READ`, dsb
- `ExpressionParserMixin`: ekspresi dengan precedence climbing

**Struktur AST** (`src/ast/`) menggunakan dataclass dengan **Visitor Pattern** (`src/ast/visitor.py`) sebagai kontrak traversal bersama antara Semantic Analyzer dan Code Generator, sehingga kedua tahap tersebut bisa menjelajahi pohon AST yang sama tanpa duplikasi logic traversal.

Dua bentuk sintaks `FUNCTION` didukung penuh (keduanya valid F77):

```fortran
INTEGER FUNCTION MULT(A, B)      ! tipe return sebagai prefix header
INTEGER A, B
MULT = A * B
END
```

```fortran
FUNCTION MULT(A, B)              ! tipe return dideklarasikan di body
INTEGER MULT, A, B
MULT = A * B
END
```

**Penanganan nested DO dengan label bersama**: Fortran 77 memperbolehkan beberapa loop `DO` bersarang berbagi satu label penutup yang sama:

```fortran
DO 10 I = 1, 3
    DO 10 J = 1, 2
        TOTAL = TOTAL + A(I,J)
10 CONTINUE
```

Parser menutup loop terdalam dahulu ketika bertemu statement berlabel `10`, lalu berkat struktur rekursif `parse_statement_list`, penutupan otomatis "menjalar" ke loop luar yang menunggu label yang sama.

### 4. Analisis Semantik

**Lokasi:** `src/semantic/`

Analisis dilakukan dalam **dua pass**:

1. **Pass deklarasi** (`_declare_subprogram`): membangun scope dan symbol table untuk *setiap* subprogram (PROGRAM, semua SUBROUTINE, semua FUNCTION) terlebih dahulu, termasuk mendaftarkan signature-nya (`ProcedureSignature`) ke tabel global.
2. **Pass pengecekan** (`_check_subprogram`): baru men-traversal body tiap subprogram untuk validasi tipe, validasi target GOTO, dsb.

Pemisahan dua pass ini penting agar **forward reference** antar subprogram bisa diresolusi dengan benar, misalnya `PROGRAM` yang memanggil `SUBROUTINE` yang didefinisikan setelahnya dalam file, atau fungsi yang me-refer ke dirinya sendiri di dalam body-nya.

Komponen utama:

- **`Scope` / `SymbolTable`**: satu `Scope` per subprogram (PROGRAM, SUBROUTINE, FUNCTION masing-masing scope terpisah dan flat, sesuai model scoping Fortran 77 yang tidak mengenal nested scope kecuali lewat `COMMON`).
- **`TypeChecker`**: validasi tipe untuk seluruh ekspresi, assignment, kondisi IF, bound DO loop, argumen pemanggilan subprogram/fungsi, dan intrinsic (`MAX`, `MIN`, `ABS`, `SQRT`, dsb) beserta aturan promosi tipe (`INTEGER`+`REAL` → `REAL`).
- **`ArrayChecker`**: validasi dimensi array harus berupa konstanta positif atau *dummy parameter* INTEGER dari subprogram yang bersangkutan (mendukung *adjustable array*, mis. `INTEGER A(N, M)` di mana `N, M` adalah parameter).
- **`CommonChecker`**: bagian paling non-trivial: nama variabel dalam satu COMMON block **boleh berbeda** antar subprogram (karena COMMON mengacu ke lokasi memori, bukan nama), tetapi **tipe dan urutan deklarasinya harus konsisten**. Checker ini membandingkan *signature* tiap anggota (tipe, rank, ukuran dimensi) posisi-demi-posisi terhadap deklarasi pertama yang ditemukan, lintas semua subprogram yang men-declare COMMON block dengan nama sama.

### 5. Code Generation

**Lokasi:** `src/codegen/`

- **`generator.py`**: orkestrator utama: forward declaration signature seluruh subprogram di awal file (memenuhi requirement "pastikan deklarasi fungsi sebelum pemanggilan"), lalu emit `PROGRAM` sebagai `int main(void)`, dan tiap `SUBROUTINE`/`FUNCTION` sebagai fungsi C dengan parameter selalu berupa pointer.
- **`arrays.py`**: menghitung offset akses array multi-dimensi. Array Fortran (column-major, 1-based) di-flatten menjadi buffer 1D C (row concept tidak relevan lagi karena sudah flat), dengan rumus:

  ```
  offset = (i₁-1) + (i₂-1)*dim₁ + (i₃-1)*dim₁*dim₂ + ...
  ```

  Untuk *adjustable array* (dimensi berupa dummy parameter), dimensi di-generate sebagai dereference pointer, mis. `(*n)`, sehingga tetap valid meski ukuran tidak diketahui saat compile time.

- **`common.py`** (`CommonBlockRegistry`): setiap COMMON block menjadi satu `struct` global C. Nama field struct diambil dari deklarasi *pertama* yang ditemukan; akses variabel COMMON di subprogram lain (meski nama lokalnya berbeda) selalu diarahkan ke *field* struct berdasarkan **indeks posisi**, bukan nama. Inilah cara transpiler menangani "reminder" pada spesifikasi bahwa COMMON block mengacu ke lokasi memori.

- **`intrinsics.py`**: pemetaan fungsi bawaan Fortran ke C: `MAX`/`MIN` → ekspresi ternary (bukan pemanggilan fungsi, sesuai catatan spesifikasi), `ABS`/`IABS` → `fabsf`/`abs` tergantung tipe, `SQRT`/`SIN`/`COS`/`TAN`/`EXP`/`LOG`/`LOG10` → varian `*f` dari `<math.h>`, `MOD` → `%` (integer) atau `fmodf` (real), `INT`/`REAL` → cast eksplisit.

- **Parameter selalu pointer**: sesuai konvensi pass-by-reference Fortran, seluruh parameter subprogram di-generate sebagai pointer C. Argumen berupa variabel biasa dikirim dengan `&`, array dikirim sebagai pointer buffer langsung (nama array itu sendiri), dan literal konstanta (mis. `CALL FOO(2, 3)`) dialokasikan ke variabel temporer dahulu (`_tmp0`, `_tmp1`, ...) sebelum diambil alamatnya, karena C tidak mengizinkan mengambil alamat dari literal.

- **DO loop dengan step negatif/dinamis**: jika step berupa konstanta, arah kondisi loop (`<=` atau `>=`) ditentukan saat compile time. Jika step berupa variabel (nilainya tidak diketahui saat transpile), kondisi di-generate sebagai ternary run-time:

  ```c
  for (i = 10; ((s) >= 0 ? (i <= n) : (i >= n)); i += s) { ... }
  ```

- **LOGICAL dicetak sebagai `T`/`F`** (bukan `1`/`0`) pada `PRINT`, mengikuti konvensi keluaran gfortran supaya output benar-benar identik dengan program Fortran asli, bagian penting untuk memenuhi requirement validasi output.

---

## Padanan Konstruksi Fortran 77 ⟺ C

| Konstruksi Fortran 77 | Padanan C | Catatan |
|---|---|---|
| `PROGRAM nama ... END` | `int main(void) { ... return 0; }` | |
| `INTEGER`/`REAL`/`LOGICAL x` | `int`/`float`/`int x;` | |
| `INTEGER A(10)` | `int a[10];` | Buffer 1D |
| `INTEGER A(3,2)` | `int a[6];` | Offset: `a[(i-1) + (j-1)*3]` |
| `COMMON /BLK/ X, Y` | `struct blk_t { int x; int y; } blk;` (global) | Field mengikuti urutan deklarasi |
| `DO 10 I=1,N ... 10 CONTINUE` | `for (i=1; i<=n; i++) { ... }` | Batas atas inklusif |
| `IF (c) THEN...ELSE...ENDIF` | `if (c) {...} else {...}` | |
| `GOTO 10` / `10 CONTINUE` | `goto L10;` / `L10: ;` | Label diberi prefix `L` |
| `SUBROUTINE nama(P1,P2) ... END` | `void nama(t1 *p1, t2 *p2) {...}` | Parameter selalu pointer |
| `T FUNCTION nama(P1) ... END` | `t nama(t1 *p1) { t nama_val; ...; return nama_val; }` | |
| `CALL SUB(A, B)` | `sub(&a, &b);` | |
| `X = MULT(A, B)` | `x = mult(&a, &b);` | |
| `.AND. .OR. .NOT.` | `&& \|\| !` | |
| `.EQ. .NE. .LT. .LE. .GT. .GE.` | `== != < <= > >=` | |
| `.TRUE. / .FALSE.` | dicetak sebagai `T`/`F` (bukan `1`/`0`) saat `PRINT` | |
| `MAX(A,B)` / `MIN(A,B)` | `((a)>(b)?(a):(b))` / `((a)<(b)?(a):(b))` | Ternary, bukan panggilan fungsi |
| `PRINT *, X, Y` | `printf("%d %f\n", x, y);` | Format menyesuaikan tipe |
| `READ *, X` | `scanf("%d", &x);` | |
| `STOP` | `exit(0);` | |

---

## Precedence Operator

Diimplementasikan di `src/parser/expressions.py` dan `precedence.py`, dari presedensi terendah ke tertinggi:

```
.OR.
.AND.
.NOT.                      (unary)
relasi (.EQ. .NE. .LT. .LE. .GT. .GE.)
+ -                        (binary, kiri-asosiatif)
* /                        (kiri-asosiatif)
+ -                        (unary)
**                         (kanan-asosiatif, mengikat lebih erat dari unary minus)
```

Contoh: `-A ** 2` diparse sebagai `-(A ** 2)`, dan `A ** B ** C` diparse sebagai `A ** (B ** C)` (right-associative), sesuai semantik Fortran.

---

## Fitur Bonus

### CHARACTER string handling

Mendukung deklarasi `CHARACTER` (default length 1, mengikuti Fortran) maupun `CHARACTER*N`. String literal disimpan sebagai `char[]` di C. Perbandingan `.EQ.`/`.NE.` antar CHARACTER di-generate menggunakan `strcmp`, dan assignment menggunakan `snprintf` dengan padding sesuai lebar kolom fixed-width khas Fortran 77.

### Computed GOTO

```fortran
GOTO (10, 20, 30), I
```

di-generate menjadi `switch` C:

```c
switch (i) {
    case 1: goto L10;
    case 2: goto L20;
    case 3: goto L30;
    default: break;
}
```

### Source Map

Flag `--source-map` menambahkan komentar `// line N` pada tiap baris hasil generate yang menunjukkan baris asal di source Fortran, memudahkan proses debugging saat membandingkan kode asli dengan hasil transpile.

---

## Pengujian

Test suite (`pytest`, 207 test) mencakup seluruh lapisan pipeline: unit test per komponen (lexer, parser, semantic, codegen) hingga **end-to-end validation** yang membandingkan output eksekusi program Fortran asli (dikompilasi dengan `gfortran`) terhadap output eksekusi hasil transpile (dikompilasi dengan `gcc`), memenuhi requirement:

> "Program hasil transpilasi dalam C harus mengeluarkan sekuens I/O ke standard output yang serupa dengan program original dalam Fortran."

Jalankan seluruh test:

```bash
pytest -v
```

### Program uji yang divalidasi end-to-end (`tests/integration/`, `tests/bonus/`)

| Program | Mencakup |
|---|---|
| `examples/hello.f` | PRINT sederhana |
| `examples/basic/fixed_form_demo.f` | Format fixed-form: komentar, continuation, label, kolom 73+ |
| `examples/basic/lexer_demo.f` | Aritmatika, IF/THEN/ELSE, operator logika, DO loop, pemanggilan SUBROUTINE |
| `examples/basic/scalar_ops.f` | Aritmatika sederhana INTEGER/REAL |
| `examples/common/sumsquares.f` | SUBROUTINE dengan parameter, COMMON block dengan nama variabel berbeda antar subprogram |
| `examples/arrays/matsum.f` | Array 2D, DO loop bersarang dengan label bersama |
| CHARACTER (`tests/bonus/test_character.py`) | Deklarasi CHARACTER, assignment, perbandingan string |
| Computed GOTO (`tests/bonus/test_computed_goto.py`) | GOTO dinamis berbasis nilai variabel |

Setiap program di atas dijalankan dua kali: sekali sebagai binary hasil `gfortran`, sekali sebagai binary hasil transpile + `gcc`, lalu output-nya dibandingkan token-per-token dengan toleransi numerik (mengakomodasi perbedaan gaya spacing/presisi antara list-directed I/O Fortran dan `printf`/`scanf` C).

---

## Cakupan dan Batasan

Sesuai spesifikasi tugas, subset yang **didukung**:

- Tipe `INTEGER`, `REAL`, `LOGICAL` (skalar dan array), serta `CHARACTER` (bonus)
- Operator aritmatika, logika, dan relasi lengkap
- Array multi-dimensi (column-major → row-major offset, 1-based → 0-based)
- `COMMON` block (struct global, field by-position)
- `DO` loop (termasuk step negatif/dinamis, nested loop dengan label bersama)
- `IF`/`THEN`/`ELSE`/`ENDIF` (block-form)
- `GOTO` + label, serta Computed GOTO (bonus)
- `PROGRAM`, `SUBROUTINE`, `FUNCTION` (kedua bentuk sintaks return type)
- Parameter selalu pass-by-reference (pointer)
- Fungsi intrinsik: `MAX`, `MIN`, `ABS`, `IABS`, `SQRT`, `EXP`, `LOG`, `LOG10`, `SIN`, `COS`, `TAN`, `MOD`, `INT`, `REAL`
- I/O dasar: `PRINT *`, `READ *`

Yang **tidak didukung** (out of scope sesuai spesifikasi): `COMPLEX`, Arithmetic IF, implicit typing, array dengan custom bound, `EQUIVALENCE`, `READ`/`PRINT` dengan format specifier, `BLOCK DATA`, alternate return, `SAVE`, statement function, file I/O eksternal, dan `WRITE`.

---

## Referensi

- Tutorial Fortran 77: <https://web.stanford.edu/class/me200c/tutorial_77/>
- Lexer generator (flex): <https://en.wikipedia.org/wiki/Flex_(lexical_analyzer_generator)>
- F2C: transpiler Fortran ke C yang sudah ada: <https://en.wikipedia.org/wiki/F2c>
- Spesifikasi Tugas Seleksi Lab IRK 2026, Ye Olde Code: Fortran to C Transpiler