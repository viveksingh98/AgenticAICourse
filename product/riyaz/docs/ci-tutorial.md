# CI seekhne ke liye — is repo ki asli failure se

Yeh tutorial theory se shuru nahi hota. Is repo mein ek GitHub Actions workflow tha jo
**March 2026 se aaj tak ek baar bhi pass nahi hua**. Usko theek karne mein maine **do galat
diagnoses** diye aur teen commits lagaye. Woh poora kissa yahan likha hai — kyunki CI seekhne
ka sabse achha tareeka yahi hai ki ek toota hua pipeline forensically kholo, aur galtiyan
kisi aur ki dekho.

Padhne ka time: ~25 min. Practice ke liye exercises aakhir mein hain.

---

## 1. CI kya hai (aur kya nahi)

**Continuous Integration** ka matlab: har push pe koi machine aapka code checkout karke kuch
checks chalati hai, aur bata deti hai ki kuch toota to nahi.

Bas itna hi. Koi jaadu nahi — bas ek dusra computer, aapke commands, har baar, bina bhoole.

**Woh cheezein jo log CI ke baare mein galat samajhte hain:**

| Galat samajh | Sach |
|---|---|
| "CI ek magic quality checker hai" | CI wahi chalata hai jo aap likhte ho. Achhe tests nahi honge to CI kuch nahi pakdega. |
| "CI green hai matlab code sahi hai" | Green ka matlab sirf itna: *jo checks aapne likhe*, woh pass hue. |
| "Mere machine pe chal raha hai to CI pe bhi chalega" | Yahi is poore tutorial ka core hai. Nahi chalega. §5 dekho. |
| "Red X hai to koi na koi dekh lega" | Nahi dekhta. Ek gate jo hamesha red ho, woh gate nahi — background noise hai. §7. |

---

## 2. Workflow file — line by line

Yeh is repo ki asli file hai, `.github/workflows/pylint.yml`:

```yaml
name: Pylint                      # Actions tab mein jo naam dikhega

on: [push]                        # kab chale — har push pe

jobs:
  check:                          # job ka id (aapka rakha hua naam)
    runs-on: ubuntu-latest        # kis machine pe — GitHub deta hai, saaf, har baar nayi
    steps:
    - uses: actions/checkout@v4   # "action" = koi aur ka likha reusable step
    - uses: actions/setup-python@v5
      with:
        python-version: "3.11"
    - name: Install dependencies  # `run` = shell command, aapka apna
      run: |
        python -m pip install --upgrade pip
        pip install pylint -r product/riyaz/grader/requirements.txt
    - name: Lint product code
      run: pylint --rcfile=product/riyaz/.pylintrc $(git ls-files 'product/riyaz/**/*.py')
```

Chaar concept, bas:

- **`on`** — trigger. `[push]`, ya `pull_request`, ya `schedule` (cron).
- **`jobs`** — har job **apni alag machine** pe chalta hai, samanantar. Ek job ki files
  doosre ko nahi milti.
- **`steps`** — ek job ke andar, kramvaar. Koi bhi step fail hua → poora job fail.
- **`uses` vs `run`** — `uses` matlab kisi aur ka banaya step; `run` matlab aapki shell command.

**Do cheezein jo shuru mein confuse karti hain:**

**Machine bilkul khaali hoti hai.** `actions/checkout` ke bina aapka code wahan hai hi nahi.
Aur jo packages aapke laptop pe pade hain, wahan nahi hain. Yeh baat §5 ka poora dhaaga hai.

**Har step fresh shell hai, par disk share hoti hai.** Ek step mein `cd` karke agle step mein
wahan hone ki umeed mat karo — par ek step mein banayi file agle step ko mil jayegi.

---

## 3. Case study: ek workflow jo kabhi pass nahi hua

Ab asli kissa. Jab maine is repo pe kaam shuru kiya, `main` pe CI red tha. Data:

| Kab | Job | Kitni der | Nateeja |
|---|---|---|---|
| 9 Mar | build (3.8) | 4s | fail — us commit pe jisne workflow add kiya |
| 27 Jul | build (3.8) | 3s | fail — **sirf markdown wale merge pe** |
| 28 Jul | build (3.11) | 8s | fail |
| 28 Jul | build (3.12) | 2s | fail |
| 28 Jul | check | 3s | fail |

**Ruko aur khud socho:** in numbers se kya pata chalta hai? Aage padhne se pehle 30 second do.

Do cheezein chikhti hain:

**Ek: 2-4 second bahut kam hai.** `pip install pylint` akele 5-10 second leta hai. Matlab job
**pip tak pahuncha hi nahi**. Failure shuruaati steps mein hai — checkout ya setup — na ki
aapke code mein.

**Do: ek markdown-only commit bhi fail hua.** Us PR mein ek bhi `.py` file nahi thi. Agar
zero Python badalne pe bhi pipeline fail hota hai, to problem **aapke code mein ho hi nahi
sakti**.

Yeh tarkeeb yaad rakho — *"kya yeh failure tab bhi hoti agar maine kuch na badla hota?"* — CI
debugging mein sabse tez sawaal yahi hai.

### Original wajah

`python-version: "3.8"` tha, `actions/setup-python@v3` ke saath.

**Python 3.8 October 2024 mein end-of-life ho gaya**, aur GitHub ne use `ubuntu-latest` runner
image se hata diya. `setup-python` ne interpreter dhoondha, nahi mila, 3 second mein mar gaya —
kisi aur step ke chalne se pehle.

Aur ek detail jo teenon jobs ko red bana rahi thi: **matrix ka `fail-fast` default `true` hota
hai.** 3.8 gira, to GitHub ne 3.9 aur 3.10 ko turant cancel kar diya. Ek missing interpreter,
teen red X.

```yaml
strategy:
  fail-fast: false      # ab har version apna nateeja khud batayega
  matrix:
    python-version: ["3.11", "3.12"]
```

---

## 4. Meri do galtiyan — aur unse kya seekhna hai

Yahin se tutorial ka sabse kaam ka hissa shuru hota hai.

### Galti 1 — sirf pylint install kiya

Pehla fix maine push kiya. Fail. Wajah:

```
product/riyaz/grader/judge.py:17:0: E0401: Unable to import 'anthropic' (import-error)
```

**Kyun:** pylint sirf text nahi padhta — woh imports **resolve** karta hai taaki bata sake ki
`obj.method()` maujood hai ya nahi. Package installed nahi hai → `E0401` → non-zero exit.

Mere laptop pe `anthropic` aur `pytest` dono installed the, isliye local pe **kabhi dikha hi
nahi**. Fix:

```yaml
pip install pylint -r product/riyaz/grader/requirements.txt
```

> **Sabak:** linter ko bhi dependencies chahiye. Aur jo package aapke machine pe "hamesha se
> hai", woh CI pe nahi hai.

### Galti 2 — logs ke bina diagnose kiya

Yeh badi galti thi.

Maine poori kahani **job durations** se banayi: 2-3 second = provision fail, 8 second = aage
badha. Theory achhi thi. Agle run ne usko tod diya — 3.11 pehle 8 second chala, phir 3 second
mein mar gaya. **Same version, same action, alag duration.** Matlab meri do explanations mein
se kam se kam ek galat thi, aur mujhe pata nahi kaunsi.

Sach yeh tha: **maine ek bhi CI log line kabhi padhi hi nahi.** Jis environment se main kaam
kar raha tha, wahan se log download har baar `HTTP 404` deta tha. Maine circumstantial evidence
se do confident diagnoses de diye, aur dono ke aadhaar pe commits push kar diye.

> **Sabak — is poore tutorial ka sabse zaroori:**
> **Logs pehle. Guess baad mein.** Duration, timing, aur "lagta hai aisa hoga" — yeh sab
> hypothesis banane ke liye theek hain, *fix push karne ke liye nahi*. Agar aapko log nahi mil
> raha, to sabse pehla kaam log tak pahunchna hai — fix likhna nahi.

Teesri baar maine push karna band kiya aur likh diya: *"mujhe log chahiye, ye rahi meri
adhoori jaankari."* Woh commit na karna hi sahi kaam tha.

### Log kahan se milta hai

1. **Actions tab → failing run → job** — pehla laal step khud khul jaata hai
2. Us step pe click → poora output
3. **Pehli error dhoondho, aakhri nahi.** Ek fail hone ke baad 200 lines cascade ho sakti hain.
4. Kuch nahi dikh raha? Job ke upar `⚙️ → Enable debug logging` karke re-run karo

---

## 5. "Mere machine pe to chalta hai" — asli wajah, aur ilaaj

Yeh CI ki sabse aam problem hai, aur iski wajah hamesha ek hi hoti hai: **aapka machine gandaa
hai, CI ka saaf.**

Aapke laptop pe pade hain: purane `pip install` se aaye packages, `.env` file, koi tool jo
aapne 8 mahine pehle daala tha, environment variables, aur ek DB file jo test ne banayi thi.
CI ke paas **kuch nahi** hai.

### Clean-room reproduction — yeh technique seekh lo

Guess karne ki jagah, apne hi machine pe CI jaisa saaf environment bana lo:

```bash
# 1. Fresh clone — aapki uncommitted files kabhi shaamil nahi
git clone <repo-url> /tmp/ci-test
cd /tmp/ci-test

# 2. Khaali virtualenv — sirf wahi jo CI install karta hai
python3.11 -m venv .venv
.venv/bin/pip install pylint -r product/riyaz/grader/requirements.txt

# 3. Bilkul wahi commands jo workflow mein likhe hain
.venv/bin/pylint --rcfile=product/riyaz/.pylintrc $(git ls-files 'product/riyaz/**/*.py')
.venv/bin/python -m pytest product/riyaz/grader/tests/ -q
```

Isi tarkeeb se maine `E0401` wali galti pakdi — mere normal environment mein woh **kabhi** nahi
dikhti.

Teen cheezein yeh pakadta hai jo aapka normal setup chhupa leta hai:

| Chhupi hui cheez | Fresh clone kaise pakadta hai |
|---|---|
| File commit karna bhool gaye | Clone mein woh file hai hi nahi |
| Koi package "hamesha se installed tha" | Khaali venv mein nahi hai |
| Test doosre test ki bachi hui DB file pe depend karta tha | Nayi directory, koi leftover nahi |

### Exit code — CI ka ekmatr signal

CI mein "pass/fail" ka matlab sirf itna hai: **command ne 0 return kiya ya nahi.** Output se
koi matlab nahi.

```bash
pytest tests/
echo "exit=$?"     # 0 = pass
```

**Ek trap jisme main khud phas gaya:**

```bash
python run_eval.py | tail -5
echo "exit=$?"     # yeh `tail` ka exit code hai, python ka nahi!
```

Pipe hamesha aakhri command ka status deta hai. Sahi tareeke:

```bash
python run_eval.py > out.txt 2>&1; echo "exit=$?"   # ya
python run_eval.py | tail -5; echo "exit=${PIPESTATUS[0]}"
```

---

## 6. Failure patterns aur unke signatures

| Kitni der lagi | Kahan fail hua | Sabse aam wajah |
|---|---|---|
| **2-5 sec** | checkout / setup se pehle ya usme | Version available nahi (jaise 3.8), permissions, quota, ya workflow syntax |
| **10-60 sec** | dependency install | Package exist nahi karta, version conflict, network |
| **1 min+** | aapke tests/lint | **Asli** failure — ab code padho |
| **Timeout (6 ghante)** | kahin bhi | Kuch input maang raha hai, ya infinite loop |

Ulta bhi: agar job **normal se bahut jaldi** fail ho, to shak pehle infrastructure pe karo,
apne code pe nahi.

**Aur teen environmental wajahein jo workflow file se theek nahi hoti** — ye maine is repo pe
flag ki thi:

- **Actions minutes / billing khatam** — har job seconds mein girta hai, content chahe kuch bhi ho
- **Fork pe Actions disabled** — forks pe default **off** hote hain (Settings → Actions → General)
- **Org policy third-party actions block kar rahi ho** — `actions/checkout` bhi nahi chalega

Teenon ka signature ek jaisa hai: sab kuch, hamesha, seconds mein. Agar aapki workflow file
theek dikhti hai aur clean-room mein commands pass karte hain, to inhe check karo.

---

## 7. Aisa CI banao jise log ignore na karein

Yeh technical se zyada design ka sawaal hai, aur zyada important hai.

Is repo mein 1,325 Python files hain. Unme se **1,317 course material** hai — bahut logon ka
likha teaching code. Pylint ke default profile pe woh **0.00/10** rate karta hai.

Do raaste the:

| Raasta | Nateeja |
|---|---|
| Poore repo pe lint chalao | Hamesha red. Sab red X ignore karna seekh jaate hain. Gate ka koi matlab nahi. |
| Sirf naye code pe lint chalao | Green hota hai, aur red hone pa **kuch matlab** rakhta hai |

Maine doosra chuna:

```yaml
- name: Lint product code
  run: pylint --rcfile=product/riyaz/.pylintrc $(git ls-files 'product/riyaz/**/*.py')
```

> **Sabak:** ek gate jo kabhi pass nahi hota, woh gate nahi hai. Woh sabko yeh sikha deta hai
> ki laal nishaan normal hai — aur phir jab **asli** bug aata hai, koi nahi dekhta.
>
> Legacy code pe CI laga rahe ho to: **naye code pe strict, purane pe abhi ke liye chhod do,**
> aur dheere-dheere daayra badhao. Din 1 pe sab kuch fix karne ki koshish ka matlab hai CI
> kabhi useful nahi banega.

Isi soch se `.pylintrc` bhi bana. Har disabled check ke saath **wajah likhi hui hai**:

```ini
[MESSAGES CONTROL]
disable =
    # Design checks: arbitrary count thresholds.
    # Ek Grade class mein 11 fields hain kyunki ek grade mein 11 cheezein record karne layak
    # hain. Linter khush karne ke liye usko todna code ko kharab karega.
    too-many-instance-attributes,
    too-many-locals,
```

Config file mein disable ke saath comment likho. Warna 6 mahine baad koi (shayad aap hi)
sochega: "yeh kyun off hai? on kar dete hain," aur 40 naye warnings aa jayenge.

---

## 8. Debugging playbook

Jab CI red ho, isi kram mein:

1. **Log padho.** Actions → run → job → pehla laal step. Guess mat karo.
2. **Poocho: "kya mere change ki wajah se hai?"** Base branch pe bhi red hai? Kya ek
   markdown-only commit bhi fail karta? Agar haan → problem aapki nahi.
3. **Duration dekho.** Bahut jaldi = infrastructure. Normal = aapka code.
4. **Clean-room mein reproduce karo.** Fresh clone + khaali venv + exact commands (§5).
5. **Reproduce ho gaya?** Ab local pe theek karo — CI push karke debug karna sabse dheema
   feedback loop hai jo maujood hai.
6. **Reproduce nahi hua?** Fark environment mein hai. Workflow mein diagnostics daalo:
   ```yaml
   - run: |
       python --version
       pip list
       ls -la
       git log --oneline -3
   ```
7. **Ek cheez badlo, ek commit.** Do fix ek saath push kiye aur phir bhi red aaya — ab pata
   nahi kaunsa kaam kiya.
8. **Do guess ke baad ruk jao.** Aur likh do ki aapko kya nahi pata. Maine teesri baar yahi
   kiya, aur wahi sahi kaam tha.

---

## 9. Exercises

Riyaz ki tarah — padhna kaafi nahi, reps chahiye.

**Ex 1 — signature padho (2 min).** Ek job 4 second mein fail hota hai. Uske steps hain:
checkout, setup-python, `pip install -r requirements.txt`, `pytest`. Kaunsa step fail hua, aur
kaise pata chala?

<details><summary>Jawab</summary>
checkout ya setup-python. `pip install` akele 4 second se zyada leta hai, to job wahan pahuncha
hi nahi. Test kabhi chala hi nahi — jo pehla shak jaata hai, woh galat jagah hai.
</details>

**Ex 2 — exit code (3 min).** Yeh CI step kabhi fail kyun nahi hoga, chahe test toot jaayein?

```yaml
- run: pytest tests/ | tee test-output.txt
```

<details><summary>Jawab</summary>
Pipe `tee` ka exit code deta hai, aur `tee` hamesha 0 return karta hai. Fix: `set -o pipefail`
lagao, ya `PIPESTATUS[0]` check karo, ya `pytest tests/ > out.txt 2>&1` likho.
</details>

**Ex 3 — clean room (15 min).** Apne kisi bhi project pe §5 wali technique chalao: fresh clone,
khaali venv, exact CI commands. Kuch toota? Jo toota, woh aapke machine pe chhupa hua tha.

**Ex 4 — apna gate banao (20 min).** Kisi purane project pe ek workflow likho jo *sirf* ek
directory pe chale. Deliberately kuch toda hua daalo, dekho red hota hai, phir theek karo aur
green dekho. Poora repo mat lo — §7 padho.

**Ex 5 — dhang se todo (10 min).** Kaam karte workflow mein ek aisi galti daalo jo *local pe
nahi dikhegi* — jaise ek package use karo jo aapke machine pe hai par `requirements.txt` mein
nahi. Push karo. Log padh ke pakdo.

---

## 10. Cheat sheet

```yaml
name: CI
on: [push, pull_request]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: "3.11"      # aisa version jo runner pe actually maujood ho
    - run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt   # linter ko bhi ye chahiye
    - run: pytest tests/ -q
    - run: pylint --rcfile=.pylintrc src/   # sirf woh code jo aap maintain karte ho
```

**Paanch baatein yaad rakhne layak:**

1. **Log padho, guess mat karo.** Log tak na pahunch pao to sabse pehla kaam wahi hai.
2. **Bahut jaldi fail = infrastructure**, aapka code nahi.
3. **"Kya yeh bina mere change ke bhi fail hota?"** — sabse tez sawaal.
4. **Clean room** hi batata hai ki aapka machine kya chhupa raha hai.
5. **Jo gate kabhi pass na ho, woh gate nahi hai.** Naye code pe strict, purane pe udaar.

---

*Yeh tutorial is repo ke `.github/workflows/pylint.yml` aur PR #2 ke asli history pe based hai.
Timings, error messages aur galtiyan — sab wahin se hain.*
