"""Checks for steps 1 and 2. Run: python3 test/run.py [base_url] [out_dir]"""
import sys, os, json
exec(open(os.path.join(os.path.dirname(__file__), 'common.py')).read())
KEY = 'composition.app.v1'
saved = lambda page: json.loads(page.evaluate(f"localStorage.getItem('{KEY}')"))
toast = lambda page: page.evaluate("document.getElementById('toast').hidden ? '' : document.getElementById('toast').textContent")

def go(page, name):
    page.evaluate("n => { location.hash = n; }", name); settle(page, name)

def location_is(page, name):
    return page.evaluate('location.hash') == '#' + name

def tab(page, name):
    page.click(f'.tab[data-tab={name}]'); settle(page, name)

def open_app(browser, w=390, h=844, **kw):
    ctx = browser.new_context(service_workers='block', viewport={'width': w, 'height': h}, **kw)
    page = ctx.new_page(); errors = []; wire(page, errors)
    page.goto(BASE); page.wait_for_selector('.page'); page.evaluate('document.fonts.ready'); page.wait_for_timeout(250)
    return ctx, page, errors

def add_lift(page, text):
    page.click('text=+ Add a lift'); settle(page, 'add')
    page.fill('.search', text); page.wait_for_timeout(60)
    page.click(f'.pick-name:text-is("{text}")'); settle(page, 'today')

SEED = """() => {
  const set = (w, r) => ({ w: String(w), r: String(r), rpe: '', done: true });
  const data = { version: 1, settings: { sound: true, units: 'lb', restSeconds: 120 }, draft: null, customLifts: [],
    pages: [{ id: 'old1', date: '2026-11-09', title: 'Chest day', startedAt: 1, filedAt: 2, unit: 'lb',
      lifts: [{ liftId: 'bench-press', sets: [set(185, 5), set(185, 5), set(185, 4)] },
              { liftId: 'db-fly', sets: [set(30, 12), set(30, 10)] },
              { liftId: 'plank', sets: [set('', 45)] }] }] };
  localStorage.setItem('composition.app.v1', JSON.stringify(data));
}"""

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])

    # ---------- every page fits, at three sizes ----------
    for label, w, h in [('phone', 390, 844), ('small', 360, 640), ('desktop', 1280, 800)]:
        ctx, page, errors = open_app(browser, w, h, device_scale_factor=2 if label != 'desktop' else 1)
        check(f'{label}: fonts loaded', page.evaluate("['Shrikhand','Bowlby One','Archivo Narrow','Special Elite','Handlee'].every(f => document.fonts.check('16px \"'+f+'\"'))"))
        page.evaluate(SEED); page.reload(); page.wait_for_selector('.page'); page.wait_for_timeout(200)
        def fits(name):
            page.wait_for_timeout(100)
            o = overflow(page)
            bad = [b for b in o['bad'] if 'chip' not in str(b) and 'sticker' not in str(b) and b != 'IMG']   # chips scroll sideways and stickers may hang off the cover, on purpose
            check(f'{label}: {name} fits the width', not bad and not o['hscroll'] and not o['doc'], json.dumps(o) if (bad or o['hscroll'] or o['doc']) else '')
            page.screenshot(path=f'{OUT}/{label}-{name}.png')
        fits('cover')
        tab(page, 'today'); fits('start')
        page.click('.repeat'); page.wait_for_selector('.title-input'); fits('writing')
        page.click('text=+ Add a lift'); settle(page, 'add'); fits('add')
        page.click('.browse > .btn'); page.click('text=+ Add helper muscles'); fits('add-new-lift')
        go(page, 'today')
        for i in range(3): page.click(f'.check >> nth={i}')
        page.click('.rest-btn'); page.wait_for_timeout(250); fits('resting'); page.click('.rest-stop')
        page.click('text=File this page'); page.click('text=Tap again to file it'); settle(page, 'filed'); page.wait_for_timeout(800); fits('filed')
        tab(page, 'notebook'); page.click('.filed-row >> nth=0'); settle(page, 'page'); fits('page')
        page.click('text=Fix this page'); page.wait_for_selector('.title-input'); fits('page-fix'); page.click('text=Back without saving')
        page.click('.lift-link >> nth=0'); settle(page, 'lift'); fits('lift')
        go(page, 'library'); fits('library')
        go(page, 'stickers'); fits('stickers')
        go(page, 'stats'); fits('stats-full')
        go(page, 'calc'); fits('calc')
        for name in ['notebook', 'stats', 'more', 'cover']:
            tab(page, name); fits(name + ('-after' if name == 'cover' else ''))
            check(f'{label}: {name} tab marked current', page.get_attribute(f'.tab[data-tab={name}]', 'aria-current') == 'page')
        imgs = page.evaluate("[...document.images].map(i => [i.src.split('/').pop(), i.complete && i.naturalWidth > 0])")
        check(f'{label}: cover art loads', imgs and all(ok for _, ok in imgs), str(imgs))
        check(f'{label}: no console errors', not errors, '; '.join(errors[:4]))
        ctx.close()

    # ---------- turning pages ----------
    ctx, page, errors = open_app(browser)
    page.click('.tab[data-tab=today]'); page.wait_for_selector('.sheet')
    mid = page.evaluate("({up: !!document.querySelector('.sheet-up'), strips: document.querySelectorAll('.sheet-strip').length, shade: !!document.querySelector('.shade.is-clearing'), below: document.querySelector('.stack > .page').dataset.page})")
    check('forward: the old page curls up in strips over the new one', mid == {'up': True, 'strips': 5, 'shade': True, 'below': 'today'}, str(mid))
    settle(page, 'today')
    page.click('.tab[data-tab=cover]'); page.wait_for_selector('.sheet')
    mid = page.evaluate("({down: !!document.querySelector('.sheet-down'), shade: !!document.querySelector('.shade.is-falling'), pages: document.querySelectorAll('.stack > .page').length})")
    check('backward: the new page falls onto the old one', mid == {'down': True, 'shade': True, 'pages': 2}, str(mid))
    settle(page, 'cover')
    flip = page.evaluate("parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--flip'))")
    check('flip is quicker than step 1', flip < 400, str(flip))
    for name in ['today', 'stats', 'notebook', 'more', 'cover', 'stats']:
        page.click(f'.tab[data-tab={name}]', no_wait_after=True)
    settle(page, 'stats')
    check('rapid taps: ends on last tab, nothing left over', page.evaluate("[document.querySelectorAll('.stack > *').length, location.hash]") == [1, '#stats'])
    tab(page, 'cover'); page.click('.cover-card .btn'); settle(page, 'today')
    check('cover button opens today', page.evaluate("location.hash") == '#today')
    page.click('#wordmark'); settle(page, 'cover')
    page.go_back(); settle(page, 'today')
    check('browser back flips back', True)
    go(page, 'stats')
    page.evaluate("location.hash = 'add'"); settle(page, 'today'); check('add a lift without a page goes to today', page.evaluate("location.hash") == '#today')
    go(page, 'stats')
    page.evaluate("location.hash = 'filed'"); settle(page, 'today'); check('page filed with nothing filed goes to today', page.evaluate("location.hash") == '#today')
    page.evaluate("location.hash = 'nonsense'"); settle(page, 'cover')
    check('unknown address falls back to cover', True)
    check('turning pages: no console errors', not errors, '; '.join(errors[:4]))
    ctx.close()

    # ---------- the verse ----------
    ctx, page, errors = open_app(browser)
    v = page.evaluate("[document.querySelector('.verse-text').textContent.length > 20, /\\d+:\\d+/.test(document.querySelector('.verse-ref').textContent)]")
    check('cover shows a verse and its reference', v == [True, True], str(v))
    ctx.close()
    seen = []
    for day in ['2026-11-12T09:00:00', '2026-11-12T23:30:00', '2026-11-13T00:10:00', '2026-11-14T12:00:00']:
        ctx = browser.new_context(service_workers='block', viewport={'width': 390, 'height': 844}); page = ctx.new_page(); errors = []; wire(page, errors)
        page.clock.set_fixed_time(day)
        page.goto(BASE); page.wait_for_selector('.verse-ref')
        seen.append(page.text_content('.verse-ref')); ctx.close()
    check('verse holds all day and changes at midnight', seen[0] == seen[1] and seen[1] != seen[2] and seen[2] != seen[3], str(seen))

    # ---------- logging a first page ----------
    ctx, page, errors = open_app(browser)
    page.add_init_script("window.__bells = 0;")
    tab(page, 'today')
    check('no past pages: no repeat list', page.locator('.repeat').count() == 0 and 'false' not in page.inner_text('.page'))
    page.fill('.write-in', 'Push day'); page.keyboard.press('Enter'); page.wait_for_selector('.title-input')
    check('typed title starts the page', page.input_value('.title-input') == 'Push day' and saved(page)['draft']['title'] == 'Push day')
    page.click('text=File this page')
    check('cannot file an empty page', toast(page) == 'Check off at least one thing first.' and saved(page)['draft'] is not None)
    add_lift(page, 'Bench Press')
    check('lift added with three open sets', page.locator('.set-row').count() == 3 and page.text_content('.lift-last') == 'first time in the notebook')
    check('first open set is the active one, with the tools under it', page.evaluate("document.querySelector('.set-row.is-active + .set-tools') !== null && document.querySelectorAll('.set-row.is-active').length === 1"))
    page.click('.check >> nth=0')
    check('checking an empty set asks for reps', toast(page) == 'Write the reps first.' and page.get_attribute('.check >> nth=0', 'aria-pressed') == 'false')
    ins = page.locator('.set-row input')
    ins.nth(0).fill('185'); ins.nth(1).fill('5'); ins.nth(2).fill('8.5')
    check('plates for 185', page.inner_text('.plates').replace('\n', ' ').upper().split() == 'EACH SIDE 45 25 ON A 45 LB BAR'.split(), page.inner_text('.plates'))
    page.click('button[aria-label="More weight"]')
    check('+5 raises the weight', ins.nth(0).input_value() == '190' and saved(page)['draft']['lifts'][0]['sets'][0]['w'] == '190')
    page.click('button[aria-label="Less weight"]'); page.click('button[aria-label="More reps"]'); page.click('button[aria-label="Fewer reps"]')
    check('steppers return to 185 x 5', [ins.nth(0).input_value(), ins.nth(1).input_value()] == ['185', '5'])
    page.click('.check >> nth=0'); page.wait_for_timeout(350)
    s0 = saved(page)['draft']['lifts'][0]['sets'][0]
    check('set checked and saved with RPE', s0 == {'w': '185', 'r': '5', 'rpe': '8.5', 'done': True}, str(s0))
    check('check mark is drawn', page.evaluate("getComputedStyle(document.querySelector('.check path')).strokeDashoffset") == '0px')
    check('next set becomes active, pencilled with the set above', page.evaluate("[...document.querySelectorAll('.set-row')].findIndex(r => r.classList.contains('is-active'))") == 1 and [ins.nth(3).get_attribute('placeholder'), ins.nth(4).get_attribute('placeholder')] == ['185', '5'])
    page.click('.check >> nth=1'); page.wait_for_timeout(100)
    check('a tap on the check takes the pencilled numbers', saved(page)['draft']['lifts'][0]['sets'][1]['w'] == '185' and ins.nth(3).input_value() == '185')
    page.click('text=+ Set'); check('add a set', page.locator('.set-row').count() == 4)
    page.click('text=− Set'); check('remove a set', page.locator('.set-row').count() == 3)
    page.click('.check >> nth=0'); check('a set can be unchecked', saved(page)['draft']['lifts'][0]['sets'][0]['done'] is False)
    page.click('.check >> nth=0')
    # a lift of your own
    page.click('text=+ Add a lift'); settle(page, 'add')
    check('lift list shows all lifts', page.locator('.pick').count() == 97, str(page.locator('.pick').count()))
    page.click('.chip:text-is("Legs")'); n_legs = page.locator('.pick').count()
    check('filter narrows the list', 0 < n_legs < 97, str(n_legs))
    check('lift already on the page is marked', page.evaluate("(document.querySelector('.chip').click(), [...document.querySelectorAll('.pick')].filter(b => b.disabled).length)") == 1)
    check('write-in button is always there', page.locator('text=+ Write in a new lift').count() == 1)
    page.fill('.search', 'Papa press')
    check('write-in button picks up the search', page.text_content('.browse > .btn') == '+ Write in a new lift: Papa press')
    page.click('.browse > .btn')
    check('form opens with the name filled in', page.input_value('.panel .write-in') == 'Papa press' and page.locator('.browse').is_hidden())
    page.click('.panel .chips:not(.muscle-chips) .chip:text-is("Chest")'); page.click('.panel .chip:text-is("Dumbbell")')
    works = '.muscle-chips[data-kind=works]'; helps = '.muscle-chips[data-kind=helps]'
    check('muscles it works: helpers are tucked away at first', page.locator(helps).is_hidden() and page.locator('text=+ Add helper muscles').is_visible())
    page.click(f'{works} .chip:text-is("Chest")'); page.click(f'{works} .chip:text-is("Triceps")')
    page.click('text=+ Add helper muscles')
    page.click(f'{helps} .chip:text-is("Front delts")'); page.click(f'{helps} .chip:text-is("Triceps")')
    check('a muscle is main or a helper, never both', page.get_attribute(f'{works} .chip:text-is("Triceps")', 'aria-pressed') == 'false' and page.get_attribute(f'{helps} .chip:text-is("Triceps")', 'aria-pressed') == 'true')
    page.click(f'{works} .chip:text-is("Triceps")')
    check('and tapping it as main takes it off the helpers', page.get_attribute(f'{helps} .chip:text-is("Triceps")', 'aria-pressed') == 'false')
    page.click('text=Add it to the page'); settle(page, 'today')
    d = saved(page)
    check('own lift is saved with its body part, gear and muscles, and added', d['customLifts'][0] == {'id': 'my-papa-press', 'name': 'Papa press', 'group': 'Chest', 'gear': 'Dumbbell', 'works': 'chest, triceps', 'helps': 'front delts'} and d['draft']['lifts'][1]['liftId'] == 'my-papa-press', str(d['customLifts']))
    check('new lift scrolls into view', page.evaluate("document.querySelector('.page').scrollTop") > 50 or page.evaluate("document.querySelector('.page').scrollHeight <= document.querySelector('.page').clientHeight + 60"))
    go(page, 'library'); page.fill('.search', 'Papa press'); page.click('.pick >> nth=0'); settle(page, 'lift')
    check('its lift page shows the muscles it works, ready to change', page.locator('.lift-muscles').count() == 1 and page.get_attribute(f'{works} .chip:text-is("Chest")', 'aria-pressed') == 'true' and 'chest, triceps' in page.inner_text('.head-block'))
    page.click(f'{works} .chip:text-is("Triceps")'); page.click(f'{works} .chip:text-is("Upper chest")')
    d = saved(page)['customLifts'][0]
    check('changing them saves at once, in the list order', d.get('works') == 'chest, upper chest' and 'chest, upper chest' in page.inner_text('.head-block'), str(d))
    for name in ['Chest', 'Upper chest']: page.click(f'{works} .chip:text-is("{name}")')
    page.click(f'{helps} .chip:text-is("Front delts")')
    d = saved(page)['customLifts'][0]
    check('clearing them all leaves the lift as it was', 'works' not in d and 'helps' not in d, str(d))
    page.click(f'{works} .chip:text-is("Chest")'); page.click(f'{works} .chip:text-is("Triceps")')
    go(page, 'library'); page.fill('.search', 'Bench Press'); page.click('.pick >> nth=0'); settle(page, 'lift')
    check('built-in lifts have no muscle chooser', page.locator('.lift-muscles').count() == 0)
    go(page, 'today')
    # draft survives a reload and shows on the cover
    page.reload(); page.wait_for_selector('.page')
    go(page, 'cover'); check('cover knows a page is in progress', page.text_content('.cover-card-title') == 'Push day' and '2 lifts so far' in page.inner_text('.cover-card'))
    tab(page, 'today'); check('draft survives a reload', page.input_value('.title-input') == 'Push day' and page.locator('.check[aria-pressed=true]').count() == 2)
    # rest timer
    page.evaluate("(() => { const d = JSON.parse(localStorage.getItem('composition.app.v1')); d.settings.restSeconds = 15; localStorage.setItem('composition.app.v1', JSON.stringify(d)); })()")
    page.reload(); page.wait_for_selector('.rest-btn')
    check('rest does not start by itself', page.evaluate("document.getElementById('rest').hidden"))
    page.click('.rest-btn'); page.wait_for_timeout(300)
    check('rest starts when pressed', page.evaluate("!document.getElementById('rest').hidden") and page.text_content('.rest-time') in ('0:15', '0:14'))
    page.click('.rest-controls button >> nth=1'); page.wait_for_timeout(250)
    check('+15 adds time', page.text_content('.rest-time') in ('0:30', '0:29'), page.text_content('.rest-time'))
    tab(page, 'notebook'); check('rest keeps running on other pages', page.evaluate("!document.getElementById('rest').hidden"))
    page.click('.rest-controls button >> nth=0'); page.click('.rest-controls button >> nth=0'); page.wait_for_timeout(1500)
    check('rest ends with its message', page.evaluate("document.getElementById('rest').classList.contains('is-over')") and page.text_content('.rest-label') == 'Rest over. Back to work.')
    tab(page, 'today'); page.click('.rest-btn'); page.click('.rest-stop')
    check('done hides the timer', page.evaluate("document.getElementById('rest').hidden"))
    # filing
    page.click('text=File this page')
    check('filing warns about unchecked sets', 'unchecked will be left off' in toast(page) and saved(page)['draft'] is not None)
    page.click('text=Tap again to file it'); settle(page, 'filed'); page.wait_for_timeout(800)
    d = saved(page); pg = d['pages'][-1]
    check('page moves to the notebook, open sets and empty lifts left off', d['draft'] is None and len(d['pages']) == 1 and len(pg['lifts']) == 1 and len(pg['lifts'][0]['sets']) == 2)
    totals = [t.replace(',', '') for t in page.locator('.total-n').all_text_contents()]
    check('totals: 1 lift, 2 sets, 1850 lb', totals[:3] == ['1', '2', '1850'], str(totals))
    check('stamp lands', page.evaluate("getComputedStyle(document.querySelector('.stamp-big')).visibility") == 'visible')
    check('first page has no records', page.locator('.record:not(.is-sticker)').count() == 0 and page.text_content('.compare-change') == 'first time')
    check('first page earns the First Page sticker', page.locator('.record.is-sticker').count() == 1 and 'First Page' in page.inner_text('.record.is-sticker') and list(saved(page)['earned']) == ['first-page'], str(saved(page)['earned']))
    tab(page, 'notebook'); check('notebook lists the page', 'Push day' in page.inner_text('.filed-list') and '1 lift · 2 sets' in page.inner_text('.filed-list'))
    go(page, 'cover'); check('cover says filed today', 'Filed today'.upper() in page.inner_text('.cover-card').upper())
    vis = page.evaluate("(s => [document.querySelectorAll('.sticker-layer .sticker').length, getComputedStyle(s).visibility === 'hidden' || s.classList.contains('is-slapped')])(document.querySelector('.sticker[aria-label=\"First Page sticker\"]'))")
    check('new sticker is slapped on the cover', vis == [5, True], str(vis))
    page.wait_for_timeout(700)
    check('sticker is on the cover', page.evaluate("getComputedStyle(document.querySelector('.sticker[aria-label=\"First Page sticker\"]')).visibility") == 'visible')
    check('first page: no console errors', not errors, '; '.join(errors[:4]))
    ctx.close()

    # ---------- repeating a page ----------
    ctx, page, errors = open_app(browser)
    page.evaluate(SEED); page.reload(); page.wait_for_selector('.page')
    tab(page, 'today')
    check('repeat is offered first', page.evaluate("document.querySelector('.repeat').compareDocumentPosition(document.querySelector('.write-in')) & 4") == 4 and 'Chest day' in page.inner_text('.repeat'))
    page.click('.repeat'); page.wait_for_selector('.title-input')
    d = saved(page)['draft']
    check('repeat copies the lifts and set counts', [l['liftId'] for l in d['lifts']] == ['bench-press', 'db-fly', 'plank'] and [len(l['sets']) for l in d['lifts']] == [3, 2, 1])
    check('last time is written under the lift', page.locator('.lift-last').first.text_content() == 'last time: 185 × 5, 5, 4', page.locator('.lift-last').first.text_content())
    ins = page.locator('.set-row input')
    check('last time is pencilled in', [ins.nth(0).get_attribute('placeholder'), ins.nth(1).get_attribute('placeholder'), ins.nth(7).get_attribute('placeholder')] == ['185', '5', '4'])
    check('timed lift counts seconds', 'SEC' in page.locator('.set-cols').nth(2).inner_text().upper())
    ins.nth(0).fill('190'); page.click('.check >> nth=0'); page.wait_for_timeout(100)
    check('beating last time is noted', page.locator('.set-note').first.text_content() == '+5 lb on last time' and 'up' in page.locator('.set-note').first.get_attribute('class'))
    check("today's weight carries down the page", ins.nth(3).get_attribute('placeholder') == '190')
    page.click('.check >> nth=1'); page.click('.check >> nth=2'); page.wait_for_timeout(100)
    notes = page.locator('.set-note:not([hidden])').all_text_contents()
    check('each set compares with the same set last time', notes == ['+5 lb on last time', '+5 lb on last time', '+5 lb on last time'], str(notes))
    page.click('.check >> nth=3'); page.wait_for_timeout(80)
    check('matching last time says so', page.locator('.set-note:not([hidden])').nth(3).text_content() == 'same as last time')
    page.click('text=File this page'); page.click('text=Tap again to file it'); settle(page, 'filed'); page.wait_for_timeout(700)
    check('record is called out', page.locator('.record:not(.is-sticker)').count() == 1 and 'Bench Press' in page.inner_text('.record:not(.is-sticker)') and 'est. max 222 lb · was 216' in page.inner_text('.record:not(.is-sticker)'), page.locator('.record').first.inner_text() if page.locator('.record').count() else 'none')
    rows = page.locator('.compare-row').all_inner_texts()
    check('each lift compares with last time', len(rows) == 2 and '+5 lb' in rows[0] and 'same' in rows[1], str(rows))
    page.screenshot(path=f'{OUT}/filed-record.png')
    # tear out
    tab(page, 'today'); page.click('.chip:text-is("Arms")'); page.wait_for_selector('.title-input')
    page.click('text=Tear out this page'); check('tear out needs two taps', saved(page)['draft'] is not None)
    page.click('text=Tap again to throw it away'); page.wait_for_selector('.write-in')
    check('page torn out', saved(page)['draft'] is None and len(saved(page)['pages']) == 2)
    check('repeating: no console errors', not errors, '; '.join(errors[:4]))
    ctx.close()

    # ---------- settings, backup, restore ----------
    ctx, page, errors = open_app(browser)
    page.evaluate(SEED); page.reload(); page.wait_for_selector('.page')
    tab(page, 'more')
    page.click('.seg[aria-label="Sound"] button:last-child')
    check('sound off saved', saved(page)['settings']['sound'] is False and toast(page) == 'Sound is off.')
    page.click('button[aria-label="Fifteen seconds longer"]')
    check('rest length changes and saves', saved(page)['settings']['restSeconds'] == 135 and page.text_content('.stepper-value') == '2:15')
    page.reload(); page.wait_for_selector('.page')
    check('settings survive a reload', page.get_attribute('.seg[aria-label="Sound"] button:last-child', 'aria-pressed') == 'true' and page.text_content('.stepper-value') == '2:15')
    tab(page, 'today'); page.click('.repeat'); page.wait_for_selector('.rest-btn')
    check('rest button shows the new length', page.text_content('.rest-btn') == 'Rest 2:15')
    tab(page, 'more')
    page.click('.seg[aria-label="Sound"] button:first-child')
    for i in range(5): page.click(f'.wrap button:nth-child({i+1})')
    page.wait_for_timeout(350)
    check('stamp appears', page.evaluate("!document.querySelector('.stamp').hidden"))
    page.click('text=Make a backup'); backup = page.input_value('textarea[readonly]'); b = json.loads(backup)
    check('backup holds pages and the page in progress', b['app'] == 'composition' and len(b['data']['pages']) == 1 and b['data']['draft']['title'] == 'Chest day')
    page.evaluate("localStorage.clear()"); page.reload(); page.wait_for_selector('.page')
    page.click('text=Restore from this backup'); check('restore: empty box refused', toast(page) == 'Paste a backup first.')
    page.fill('textarea:not([readonly])', 'hello there'); page.click('text=Restore from this backup')
    check('restore: junk refused', toast(page) == "That doesn't look like a Composition backup.")
    page.fill('textarea:not([readonly])', backup); page.click('text=Restore from this backup')
    check('restore: first tap only arms', len(saved(page)['pages']) == 0)
    page.click('text=Tap again to replace everything'); page.wait_for_timeout(200)
    check('restore: second tap brings everything back', len(saved(page)['pages']) == 1 and saved(page)['draft']['title'] == 'Chest day' and saved(page)['settings']['restSeconds'] == 135)
    page.evaluate(f"localStorage.setItem('{KEY}', '{{not json')"); page.reload(); page.wait_for_selector('.page')
    check('damaged save: app still opens', page.locator('.stack > .page').count() == 1)
    page.evaluate(f"localStorage.setItem('{KEY}', JSON.stringify({{version:1, settings:{{sound:true}}, pages:[]}}))"); page.reload(); page.wait_for_selector('.page')
    tab(page, 'today'); check('a step 1 save still opens', page.locator('.write-in').count() == 1)
    check('settings: no console errors', not errors, '; '.join(errors[:4]))
    ctx.close()

    # ---------- stickers on the cover ----------
    ctx, page, errors = open_app(browser)
    check('four stickers come with the notebook', page.locator('.sticker-layer .sticker').count() == 4)
    boxes = page.evaluate("[...document.querySelectorAll('.sticker-layer .sticker')].map(s => { const r = s.getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; })")
    spread = max(b[1] for b in boxes) - min(b[1] for b in boxes)
    check('stickers are scattered, not in a row', spread > 120 and min(b[2] for b in boxes) >= 100, str([[round(v) for v in b] for b in boxes]))
    over = page.evaluate("""() => { const hit = (a, b) => a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom;
      const others = [document.querySelector('.verse'), document.querySelector('.cover-card')].map(e => e.getBoundingClientRect());
      return [...document.querySelectorAll('.sticker-layer .sticker')].filter(s => others.some(o => hit(s.getBoundingClientRect(), o))).length; }""")
    check('some stickers overlap the verse or the card', over >= 2, str(over))
    check('the today card is small', page.evaluate("document.querySelector('.cover-card').offsetHeight") < 90)
    btn = page.locator('.cover-card .btn').bounding_box()
    covered = page.evaluate("([x, y]) => !!document.elementFromPoint(x, y).closest('.cover-card .btn')", [btn['x'] + btn['width'] / 2, btn['y'] + btn['height'] / 2])
    check('no sticker covers the open button', covered)
    g = page.locator('.sticker[aria-label="Hanging Gloves sticker"]'); b0 = g.bounding_box()
    page.mouse.move(b0['x'] + b0['width'] / 2, b0['y'] + b0['height'] / 2); page.mouse.down()
    page.mouse.move(b0['x'] + b0['width'] / 2 + 120, b0['y'] + b0['height'] / 2 + 90, steps=8); page.mouse.up()
    b1 = g.bounding_box(); pos = saved(page)['stickers'].get('gloves')
    check('a sticker can be dragged', abs(b1['x'] - b0['x'] - 120) < 6 and abs(b1['y'] - b0['y'] - 90) < 6 and pos is not None, str(pos))
    page.reload(); page.wait_for_selector('.sticker-layer .sticker'); page.wait_for_timeout(200)
    b2 = page.locator('.sticker[aria-label="Hanging Gloves sticker"]').bounding_box()
    check('it stays where it was put', abs(b2['x'] - b1['x']) < 3 and abs(b2['y'] - b1['y']) < 3, f"{b1} {b2}")
    page.locator('.sticker[aria-label="Contest Ribbons sticker"]').click()
    check('a tap names the sticker', toast(page) == 'Contest Ribbons')
    tab(page, 'today'); tab(page, 'cover')
    b3 = page.locator('.sticker[aria-label="Hanging Gloves sticker"]').bounding_box()
    check('place survives a page flip', abs(b3['x'] - b1['x']) < 3 and abs(b3['y'] - b1['y']) < 3)
    # the sticker book
    tab(page, 'more'); check('more shows the sticker count', '4 of 21 earned' in page.inner_text('.panel >> nth=0'))
    page.click('a[href="#stickers"]'); settle(page, 'stickers')
    check('book lists every sticker, most still locked', page.locator('.book-card').count() == 21 and page.locator('.book-card.is-locked').count() == 17)
    check('locked stickers say how to earn them', 'Bench press 225 lb.' in page.inner_text('.book'))
    page.click('.book-card >> nth=0')
    check('a sticker can be peeled off the cover', saved(page)['stickers']['gloves'].get('off') is True and 'peeled off' in page.inner_text('.book-card >> nth=0'))
    go(page, 'cover'); check('peeled sticker is gone from the cover', page.locator('.sticker-layer .sticker').count() == 3)
    go(page, 'stickers'); page.click('.book-card >> nth=0'); go(page, 'cover')
    check('and stuck back on, in the same place', page.locator('.sticker-layer .sticker').count() == 4 and abs(page.locator('.sticker[aria-label="Hanging Gloves sticker"]').bounding_box()['x'] - b1['x']) < 3)
    check('stickers: no console errors', not errors, '; '.join(errors[:4]))
    ctx.close()

    # ---------- earning stickers ----------
    EARN = """() => {
      const set = (w, r) => ({ w: String(w), r: String(r), rpe: '', done: true });
      const day = n => '2026-10-' + String(n).padStart(2, '0');
      const page = (n, lifts, cardio) => ({ id: 'p' + n, date: day(n), title: 'Day ' + n, startedAt: 1, filedAt: 2, unit: 'lb', lifts, cardio: cardio || [] });
      const bag = { kindId: 'heavy-bag', values: { rounds: '6', minutes: '18' }, done: true };
      const run = miles => ({ kindId: 'running', values: { miles: String(miles), minutes: '30' }, done: true });
      const pages = [
        page(1, [{ liftId: 'squat', sets: [set(365, 3)] }], [bag, run(4)]),
        page(3, [{ liftId: 'bench-press', sets: [set(245, 2)] }], [bag, run(3)]),
        page(5, [{ liftId: 'deadlift', sets: [set(455, 1)] }], [bag]),
        page(12, [], [bag, run(3.5)]),
        page(20, [], [bag]),
      ];
      localStorage.setItem('composition.app.v1', JSON.stringify({ version: 1, settings: { sound: true, units: 'lb', restSeconds: 120 }, draft: null, customLifts: [], pages }));
    }"""
    ctx, page, errors = open_app(browser)
    page.evaluate(EARN); page.reload(); page.wait_for_selector('.page'); page.wait_for_timeout(900)
    earned = sorted(saved(page)['earned'])
    want = sorted(['first-page', 'week-3', 'bench-225', 'squat-315', 'dead-405', 'club-1000', 'bag-5', 'road-10'])
    check('past training earns the right stickers', earned == want, str(earned))
    check('not the ones still out of reach', 'pages-10' not in earned and 'record' not in earned)
    check('earned stickers are on the cover', page.locator('.sticker-layer .sticker').count() == 12)
    page.screenshot(path=f'{OUT}/cover-full.png')
    check('earning: no console errors', not errors, '; '.join(errors[:4]))
    ctx.close()

    # ---------- cardio ----------
    ctx, page, errors = open_app(browser)
    tab(page, 'today'); page.click('.chip:text-is("Boxing")'); page.wait_for_selector('.title-input')
    check('cardio choices stay closed until asked for', page.locator('.page-actions .chips').is_hidden())
    page.click('text=+ Add cardio')
    check('cardio button sits under add a lift', page.evaluate("document.querySelector('a[href=\"#add\"]').nextElementSibling.textContent") == '+ Add cardio' and page.locator('.page-actions .chip').count() == 12)
    page.click('.chip:text-is("Heavy Bag")')
    check('boxing is added, marked in purple', page.locator('.cardio.is-boxing').count() == 1 and page.locator('.cardio-box').all_inner_texts() == ['ROUNDS', 'MIN'] or [t.upper() for t in page.locator('.cardio-box').all_inner_texts()] == ['ROUNDS', 'MIN'])
    page.click('.cardio .check')
    check('cardio needs a number before it can be checked', toast(page) == 'Write a number first.' and saved(page)['draft']['cardio'][0]['done'] is False)
    cb = page.locator('.cardio-box input'); cb.nth(0).fill('6'); cb.nth(1).fill('18')
    page.click('.cardio .check')
    page.click('text=+ Add cardio'); page.click('.chip:text-is("Running")')
    check('running asks for miles and minutes', [t.upper() for t in page.locator('.cardio >> nth=1').locator('.cardio-box').all_inner_texts()] == ['MI', 'MIN'])
    d = saved(page)['draft']
    check('cardio is saved on the page', d['cardio'][0] == {'kindId': 'heavy-bag', 'values': {'rounds': '6', 'minutes': '18'}, 'done': True} and d['cardio'][1]['kindId'] == 'running', str(d['cardio']))
    page.reload(); page.wait_for_selector('.cardio'); check('cardio survives a reload', page.locator('.cardio').count() == 2 and page.locator('.cardio .check[aria-pressed=true]').count() == 1)
    page.click('text=File this page'); page.click('text=Tap again to file it'); settle(page, 'filed'); page.wait_for_timeout(700)
    pg = saved(page)['pages'][-1]
    check('a page with only cardio can be filed; unchecked cardio is left off', len(pg['lifts']) == 0 and len(pg['cardio']) == 1)
    check('filed page lists the cardio', '6 rounds · 18 min' in page.inner_text('.page') and 'Heavy Bag' in page.inner_text('.page'))
    tab(page, 'notebook'); check('notebook mentions the cardio', 'heavy bag' in page.inner_text('.filed-list'))
    tab(page, 'today'); page.click('.repeat'); page.wait_for_selector('.cardio')
    check('repeating a page brings its cardio back, empty', saved(page)['draft']['cardio'] == [{'kindId': 'heavy-bag', 'values': {}, 'done': False}])
    check('cardio: no console errors', not errors, '; '.join(errors[:4]))
    ctx.close()

    # ---------- step 3: looking back ----------
    HISTORY = """() => {
      const set = (w, r) => ({ w: String(w), r: String(r), rpe: '', done: true });
      const benches = [[185,5],[190,5],[195,5],[200,4],[205,5]];
      const pages = benches.map(([w, r], i) => ({ id: 'h' + i, date: '2026-10-' + String(1 + i * 7).padStart(2, '0'),
        title: 'Chest day', startedAt: 0, filedAt: 3600000, unit: 'lb',
        lifts: [{ liftId: 'bench-press', sets: [set(w, r), set(w, r)] }, { liftId: 'db-fly', sets: [set(30, 12)] }],
        cardio: i === 4 ? [{ kindId: 'heavy-bag', values: { rounds: '6', minutes: '18' }, done: true }] : [] }));
      localStorage.setItem('composition.app.v1', JSON.stringify({ version: 1, settings: { sound: true, units: 'lb', restSeconds: 120 }, draft: null, customLifts: [], pages }));
    }"""
    ctx, page, errors = open_app(browser)
    page.evaluate(HISTORY); page.reload(); page.wait_for_selector('.page')
    tab(page, 'notebook')
    check('notebook lists pages newest first, each one opens', page.locator('.filed-row').count() == 5 and page.locator('.filed-row .kicker').first.text_content() == 'Thu · Oct 29')
    page.click('.filed-row >> nth=0'); settle(page, 'page')
    check('a filed page opens read-only', page.locator('.page input').count() == 0 and page.locator('text=Fix this page').count() == 1)
    check('it shows every set and the cardio', '205 × 5, 5' in page.inner_text('.page') and '6 rounds · 18 min' in page.inner_text('.page'))
    page.click('text=Fix this page'); page.wait_for_selector('.title-input')
    check('fixing opens the boxes', page.locator('.set-row input').count() == 9)
    page.fill('.title-input', 'Heavy chest'); ins = page.locator('.set-row input'); ins.nth(0).fill('210')
    page.click('text=Back without saving'); page.wait_for_selector('.lift-link')
    check('backing out keeps the page as it was', saved(page)['pages'][4]['lifts'][0]['sets'][0]['w'] == '205' and saved(page)['pages'][4]['title'] == 'Chest day')
    page.click('text=Fix this page'); page.wait_for_selector('.title-input')
    page.fill('.title-input', 'Heavy chest'); page.locator('.set-row input').nth(0).fill('210')
    page.click('text=Save the fixes'); page.wait_for_selector('.lift-link')
    pg5 = saved(page)['pages'][4]
    check('saving fixes the page and works its records out again', pg5['title'] == 'Heavy chest' and pg5['lifts'][0]['sets'][0]['w'] == '210' and pg5['summary']['records'][0]['now'] == 245, str(pg5['summary']['records']))
    check('fixed page reads back with the new numbers', 'Heavy chest' in page.text_content('.heading') and '210 × 5' in page.inner_text('.page'))
    page.click('.lift-link >> nth=0'); settle(page, 'lift')
    check('from a page, back says back to the page', page.locator('a[href="#page"]').count() == 1)
    check('a lift name opens its history', page.text_content('.heading') == 'Bench Press' and page.locator('.chart svg').count() == 1)
    check('history shows the best numbers', [t.replace('\n', ' ') for t in page.locator('.total-n').all_inner_texts()] == ['245 lb', '210 lb'], str(page.locator('.total-n').all_inner_texts()))
    check('the chart plots every page and rings the best', page.locator('.chart circle').count() == 5 and page.locator('.chart ellipse').count() == 1)
    page.click('.chart .chip:text-is("Heaviest weight")')
    check('the chart switches to heaviest weight', 'Heaviest weight' in page.text_content('.chart .kicker') and '210' in page.inner_text('.chart'))
    rows = page.locator('.session-row').count()
    check('every session is listed, newest first', rows == 5 and 'OCT 29' in page.locator('.session-row').first.inner_text().upper())
    page.click('.session-row >> nth=4'); settle(page, 'page')
    check('a session opens its page', 'Oct 1' in page.text_content('.page .kicker'))
    go(page, 'notebook'); page.click('text=The lift library'); settle(page, 'library')
    check('library puts logged lifts first', page.locator('.pick-name').first.text_content() == 'Bench Press' and '5 pages' in page.locator('.pick').first.inner_text())
    page.fill('.search', 'row'); check('library search', all('row' in t.lower() for t in page.locator('.pick-name').all_text_contents()) and page.locator('.pick').count() > 0)
    page.click('.pick >> nth=0'); settle(page, 'lift')
    check('from the library, back goes to the library', page.locator('a[href="#library"]').count() == 1)
    check('a lift never logged says so', 'Not in the notebook yet' in page.inner_text('.page'))
    go(page, 'notebook'); page.click('.filed-row >> nth=0'); settle(page, 'page')
    page.click('text=Repeat this page'); settle(page, 'today')
    check('repeat from an old page starts today with its lifts', [l['liftId'] for l in saved(page)['draft']['lifts']] == ['bench-press', 'db-fly'])
    go(page, 'notebook'); page.click('.filed-row >> nth=1'); settle(page, 'page')
    page.click('text=Repeat this page')
    check('cannot repeat while a page is open today', toast(page) == "Finish today's page first." and location_is(page, 'page'))
    page.click('.page-actions .link-btn'); page.click('text=Tap again to throw it away'); settle(page, 'notebook')
    check('a page can be torn out of the notebook', len(saved(page)['pages']) == 4)
    page.reload(); page.wait_for_selector('.page')
    page.evaluate("location.hash = 'page'"); settle(page, 'notebook')
    check('an old page address after a reload goes to the notebook', True)
    check('step 3: no console errors', not errors, '; '.join(errors[:4]))
    ctx.close()

    # ---------- tougher stickers ----------
    STRONG = """() => {
      const set = (w, r) => ({ w: String(w), r: String(r), rpe: '', done: true });
      const lifts = [{ liftId: 'squat', sets: [set(405, 1)] }, { liftId: 'bench-press', sets: [set(275, 1), set(225, 12)] }, { liftId: 'deadlift', sets: [set(500, 1)] }];
      const pages = [{ id: 's1', date: '2026-10-01', title: 'Heavy', startedAt: 0, filedAt: 1, unit: 'lb', lifts, cardio: [] }];
      localStorage.setItem('composition.app.v1', JSON.stringify({ version: 1, settings: { sound: true, units: 'lb', restSeconds: 120 }, draft: null, customLifts: [], pages }));
    }"""
    ctx, page, errors = open_app(browser)
    page.evaluate(STRONG); page.reload(); page.wait_for_selector('.page'); page.wait_for_timeout(300)
    e = saved(page)['earned']
    check('clubs count real lifts: 1180 earns the 1000 club only', 'club-1000' in e and 'club-1250' not in e, str(sorted(e)))
    check('an estimated max does not earn a club', 'club-1500' not in e)
    check('no bodyweight stickers until bodyweight is set', not any(k.startswith('bw-') for k in e))
    tab(page, 'stats'); page.fill('.weigh-in', '180'); page.click('.weigh-row .btn'); page.wait_for_timeout(250)
    e = saved(page)['earned']
    check('weighing in earns the ones already lifted', 'bw-bench' in e and 'bw-squat' in e and 'bw-dead' in e and saved(page)['weighins'][-1]['w'] == 180, str(sorted(e)))
    check('and says so', 'New sticker' in toast(page))
    page.evaluate("""() => { const d = JSON.parse(localStorage.getItem('composition.app.v1'));
      d.pages[0].lifts[1].sets.push({ w: '225', r: '12', rpe: '', done: true });
      localStorage.setItem('composition.app.v1', JSON.stringify(d)); }""")
    page.reload(); page.wait_for_selector('.page')
    check('a million pounds is still far off', 'million' not in saved(page)['earned'])
    page.evaluate("""() => { const d = JSON.parse(localStorage.getItem('composition.app.v1'));
      const set = { w: '400', r: '10', rpe: '', done: true };
      for (let i = 0; i < 250; i++) d.pages.push({ id: 'm' + i, date: '2026-11-01', title: 'Volume', startedAt: 0, filedAt: 1, unit: 'lb', lifts: [{ liftId: 'squat', sets: [set] }], cardio: [] });
      localStorage.setItem('composition.app.v1', JSON.stringify(d)); }""")
    page.reload(); page.wait_for_selector('.page')
    check('a million pounds moved earns its sticker', 'million' in saved(page)['earned'])
    check('stickers: no console errors', not errors, '; '.join(errors[:4]))
    ctx.close()

    # ---------- the round timer ----------
    ctx = browser.new_context(service_workers='block', viewport={'width': 390, 'height': 844})
    page = ctx.new_page(); errors = []; wire(page, errors)
    page.clock.install()
    page.add_init_script("""window.__sounds = [];""")
    page.goto(BASE); page.wait_for_selector('.page')
    page.evaluate("""() => { const d = { version: 1, settings: { sound: true, units: 'lb', restSeconds: 120, roundCount: 2, roundSeconds: 30, breakSeconds: 15 }, draft: null, customLifts: [], pages: [] };
      localStorage.setItem('composition.app.v1', JSON.stringify(d)); }""")
    page.reload(); page.wait_for_selector('.page')
    tab(page, 'more')
    check('round settings show', '2×' in page.inner_text('.page') and '0:30' in page.inner_text('.page'))
    page.click('button[aria-label="One round more"]')
    check('round count changes and saves', saved(page)['settings']['roundCount'] == 3)
    page.click('button[aria-label="One round fewer"]')
    tab(page, 'today'); page.click('.chip:text-is("Boxing")'); page.wait_for_selector('.title-input')
    page.click('text=+ Add cardio'); page.click('.chip:text-is("Heavy Bag")')
    check('a boxing entry has a round timer button', page.text_content('.cardio .btn-small') == 'Rounds 2 × 0:30')
    page.click('.cardio .btn-small'); page.clock.run_for(500)
    check('round 1 starts', page.text_content('.rest-label') == 'Round 1 of 2' and page.evaluate("document.getElementById('rest').classList.contains('is-rounds')"))
    page.clock.run_for(30500)
    check('the break follows the round', page.text_content('.rest-label') == 'Break · Round 2 next' and page.evaluate("document.getElementById('rest').classList.contains('is-break')"))
    check('the finished round is written in', page.input_value('.cardio-box input >> nth=0') == '1' and saved(page)['draft']['cardio'][0]['values']['rounds'] == '1')
    tab(page, 'notebook')
    page.clock.run_for(15500)
    check('round 2 runs while you are on another page', page.text_content('.rest-label') == 'Round 2 of 2')
    page.clock.run_for(30500)
    check('after the last round it says so', page.text_content('.rest-label') == '2 rounds done. Good work.')
    tab(page, 'today')
    check('both rounds and the minutes are written in', [page.input_value('.cardio-box input >> nth=0'), page.input_value('.cardio-box input >> nth=1')] == ['2', '1'])
    page.clock.run_for(7000)
    check('the bar tucks away after', page.evaluate("document.getElementById('rest').hidden"))
    page.click('.cardio .btn-small'); page.clock.run_for(5000); page.click('.rest-stop')
    check('done stops the rounds early', page.evaluate("document.getElementById('rest').hidden") and saved(page)['draft']['cardio'][0]['values']['rounds'] == '2')
    check('round timer: no console errors', not errors, '; '.join(errors[:4]))
    ctx.close()

    # ---------- round 5: quick turns, notes, this week, poses ----------
    ctx, page, errors = open_app(browser)
    page.evaluate(SEED); page.reload(); page.wait_for_selector('.page')
    page.click('.tab[data-tab=today]'); page.wait_for_selector('.sheet')
    check('the cover turns with the full curl', page.evaluate("!document.querySelector('.sheet').classList.contains('is-quick')"))
    settle(page, 'today')
    page.click('.tab[data-tab=notebook]'); page.wait_for_selector('.page.turn-up')
    dur = page.evaluate("getComputedStyle(document.querySelector('.page.turn-up')).animationDuration")
    check('inner pages turn quickly, as the real page with no copies', dur == '0.18s' and page.locator('.sheet').count() == 0 and page.locator('.stack > .page').count() == 2, dur)
    settle(page, 'notebook')
    check('this week shows seven days with today circled', page.locator('.week-day').count() == 7 and page.locator('.week-day.is-today').count() == 1)
    tab(page, 'today'); page.click('.repeat'); page.wait_for_selector('.title-input')
    check('a lift with no note offers one', page.locator('.lift >> nth=0').locator('.lift-head .note-shown.is-empty').count() == 1)
    page.click('.note-shown >> nth=0'); page.keyboard.type('Elbows tucked, pause on the chest')
    page.click('.note-done'); page.wait_for_timeout(400)
    check('a note saves to the lift', saved(page)['liftNotes'].get('bench-press') == 'Elbows tucked, pause on the chest')
    check('it reads back in pen', page.text_content('.note-shown >> nth=0') == 'Elbows tucked, pause on the chest')
    check('chest page gets the chest pose', 'sketch-front' in page.get_attribute('.sketch-pose', 'src'))
    sk = page.locator('.sketch-pose').bounding_box(); lh = page.locator('.lift >> nth=0').bounding_box()
    check('the sketch stays clear of the first lift', sk['y'] + sk['height'] <= lh['y'] + 6, f"{sk} {lh}")
    go(page, 'notebook'); page.click('text=The lift library'); settle(page, 'library'); page.click('.pick >> nth=0'); settle(page, 'lift')
    check('the note shows on the lift history too', 'Elbows tucked' in page.inner_text('.lift-notes'))
    page.click('.lift-notes .note-shown'); page.fill('.lift-notes .note-box', ''); page.click('.lift-notes .note-done'); page.wait_for_timeout(400)
    check('clearing a note removes it', 'bench-press' not in saved(page)['liftNotes'])
    go(page, 'today')
    for i in range(3): page.click(f'.check >> nth={i}')
    page.click('text=File this page'); page.click('text=Tap again to file it'); settle(page, 'filed'); page.wait_for_timeout(500)
    go(page, 'notebook')
    check('a page filed today is marked in this week', page.locator('.week-day.is-today .week-mark.is-lift').count() == 1 and '2 days in' in page.inner_text('.week-box'))
    page.click('.week-day.is-today'); settle(page, 'page')
    check('tapping a marked day opens its page', 'Chest day' in page.text_content('.heading'))
    check('round 5: no console errors', not errors, '; '.join(errors[:4]))
    ctx.close()

    # ---------- step 5: stats ----------
    STATS = """() => {
      const set = (w, r) => ({ w: String(w), r: String(r), rpe: '', done: true });
      const pages = [
        { id: 'a', date: '2026-10-05', title: 'Leg day', startedAt: 0, filedAt: 1, unit: 'lb', lifts: [{ liftId: 'squat', sets: [set(315, 5)] }], cardio: [] },
        { id: 'b', date: '2026-10-12', title: 'Chest day', startedAt: 0, filedAt: 1, unit: 'lb', lifts: [{ liftId: 'bench-press', sets: [set(225, 5)] }, { liftId: 'db-fly', sets: [set(35, 12)] }], cardio: [{ kindId: 'heavy-bag', values: { rounds: '6' }, done: true }] },
        { id: 'c', date: '2026-10-19', title: 'Back day', startedAt: 0, filedAt: 1, unit: 'lb', lifts: [{ liftId: 'deadlift', sets: [set(405, 3)] }], cardio: [],
          summary: { records: [{ name: 'Deadlift', now: 446, was: 430 }] } },
        { id: 'd', date: '2026-11-02', title: 'Leg day', startedAt: 0, filedAt: 1, unit: 'lb', lifts: [{ liftId: 'squat', sets: [set(335, 3)] }], cardio: [] },
      ];
      localStorage.setItem('composition.app.v1', JSON.stringify({ version: 1, settings: { sound: true, units: 'lb', restSeconds: 120 }, draft: null, customLifts: [], pages, weighins: [{ date: '2026-10-01', w: 181 }] }));
    }"""
    ctx, page, errors = open_app(browser)
    page.evaluate("localStorage.setItem('composition.app.v1', JSON.stringify({ version: 1, settings: { bodyweight: 181 }, pages: [] }))"); page.reload(); page.wait_for_selector('.page')
    check('an old bodyweight setting becomes a weigh-in', saved(page)['weighins'][0]['w'] == 181 and 'bodyweight' not in saved(page)['settings'])
    page.evaluate(STATS); page.reload(); page.wait_for_selector('.page')
    tab(page, 'stats')
    cards = page.locator('.b3-row').all_inner_texts()
    check('the Big Three show their maxes, marked as estimated', '369' in cards[0] and 'ESTIMATED' in cards[0].upper() and '263' in cards[1] and '446' in cards[2], str([c[:60] for c in cards]))
    check('levels wait for the standards to be picked', page.locator('.level').count() == 0 and 'Pick the standards' in page.inner_text('.page'))
    page.click('.standards-row .chip:text-is("Men")'); page.wait_for_selector('.level')
    check('picking standards saves and shows levels', saved(page)['settings']['sex'] == 'men' and page.locator('.level').count() == 3)
    lv = page.locator('.b3-row >> nth=1').inner_text()
    check('bench 263 at 181 lb is Advanced, with pounds to Elite', 'ADVANCED' in lv.upper() and 'lb to Elite' in lv, lv)
    tot = page.inner_text('.b3-total')
    check('total is the heaviest three: 335 + 225 + 405 = 965', '965' in tot)
    check('Wilks and DOTS are worked out', '297.' in tot or '298.' in tot or '296.' in tot, tot)
    check('the chart starts on a lift with two pages', page.locator('.stats-part >> nth=0').locator('.chart svg').count() == 1)
    page.click('.stats-part >> nth=0 >> .chip:text-is("Bench Press")')
    check('a lift with one page says it needs another', 'Two pages with a lift' in page.inner_text('.stats-part >> nth=0'))
    page.fill('.weigh-in', '179.4'); page.click('.weigh-row .btn'); page.wait_for_timeout(300)
    wi = saved(page)['weighins']
    check('weighing in saves today', wi[-1]['w'] == 179.4 and len(wi) == 2)
    page.fill('.weigh-in', '179'); page.keyboard.press('Enter'); page.wait_for_timeout(300)
    check('a second weigh-in today replaces the first', len(saved(page)['weighins']) == 2 and saved(page)['weighins'][-1]['w'] == 179)
    page.fill('.weigh-in', 'abc'); page.click('.weigh-row .btn')
    check('a weigh-in needs a number', toast(page) == 'Write your weight first.')
    check('bodyweight chart appears with two weigh-ins', page.locator('.stats-part >> nth=1').locator('svg').count() == 1)
    page.locator('.stats-part >> nth=1').locator('.lift-remove').first.click(); page.locator('.stats-part >> nth=1').locator('text=Tap again').click(); page.wait_for_timeout(200)
    check('a weigh-in can be removed', len(saved(page)['weighins']) == 1)
    cal = page.locator('.cal-box')
    check('calendar opens on this month', 'November 2026' in cal.inner_text() and cal.locator('.cal-day.has-page').count() == 1)
    page.click('button[aria-label="Earlier month"]')
    check('it goes back a month, marking lifting and boxing', 'October 2026' in page.inner_text('.cal-box') and page.locator('.cal-box .cal-day.has-page').count() == 3 and page.locator('.cal-box .week-mark.is-box').count() == 1)
    page.locator('.cal-box .cal-day.has-page').first.click(); settle(page, 'page')
    check('a calendar day opens its page', 'Leg day' in page.text_content('.heading'))
    go(page, 'stats')
    check('records are pinned with their ribbons', page.locator('.record-row').count() == 1 and 'Deadlift' in page.inner_text('.record-row') and page.locator('.record-row img').count() == 1)
    page.click('text=Try any numbers'); settle(page, 'calc')
    vals = [page.locator('.calc-in').nth(i).input_value() for i in range(4)]
    check('calculator starts from your numbers', vals == ['181', '335', '225', '405'], str(vals))
    page.locator('.calc-in').nth(2).fill('330'); page.wait_for_timeout(100)
    out = page.inner_text('.calc-out')
    check('trying a 330 bench updates the total and level', '1070' in out and 'ELITE' in out.upper(), out[:200])
    check('nothing in the calculator is saved', all(s.get('w') != '330' for p in saved(page)['pages'] for e in p['lifts'] for s in e['sets']))
    page.click('.calc-out ~ * >> text=nothing', timeout=100) if False else None
    page.click('.standards-row .chip:text-is("Women")'); page.wait_for_timeout(80)
    check('switching standards changes the levels and scores', 'WORLD CLASS' in page.inner_text('.calc-out').upper() or 'ELITE' in page.inner_text('.calc-out').upper())
    check('the switch in the calculator is not saved', saved(page)['settings']['sex'] == 'men')
    page.click('text=Use my numbers')
    check('use my numbers resets it', page.locator('.calc-in').nth(2).input_value() == '225' and page.get_attribute('.standards-row .chip:text-is("Men")', 'aria-pressed') == 'true')
    check('step 5: no console errors', not errors, '; '.join(errors[:4]))
    ctx.close()

    # ---------- a note for today ----------
    ctx, page, errors = open_app(browser)
    page.evaluate(SEED); page.reload(); page.wait_for_selector('.page')
    tab(page, 'today'); page.click('.repeat'); page.wait_for_selector('.title-input')
    page.locator('.day-note .note-shown').first.click(); page.keyboard.type('Left shoulder felt off'); page.locator('.day-note .note-done').first.click(); page.wait_for_timeout(400)
    check('a note for today saves on the lift', saved(page)['draft']['lifts'][0].get('note') == 'Left shoulder felt off')
    for i in range(3): page.click(f'.check >> nth={i}')
    page.click('text=File this page'); page.click('text=Tap again to file it'); settle(page, 'filed'); page.wait_for_timeout(400)
    check('it is filed with the page', saved(page)['pages'][-1]['lifts'][0].get('note') == 'Left shoulder felt off')
    go(page, 'notebook'); page.click('.filed-row >> nth=0'); settle(page, 'page')
    check('it shows on the filed page', 'Left shoulder felt off' in page.inner_text('.page'))
    page.click('.lift-link >> nth=0'); settle(page, 'lift')
    check('and beside that session in the history', 'Left shoulder felt off' in page.inner_text('.session-row >> nth=0'))
    check('day notes: no console errors', not errors, '; '.join(errors[:4]))
    ctx.close()

    # ---------- round 7: fixes, tested maxes, units, the garage ----------
    ctx, page, errors = open_app(browser)
    tab(page, 'today'); page.fill('.write-in', 'Upper body power and conditioning'); page.keyboard.press('Enter'); page.wait_for_selector('.title-input')
    box = page.locator('.title-input')
    check('a long title wraps instead of cutting off', box.input_value() == 'Upper body power and conditioning' and page.evaluate("(b => b.scrollHeight <= b.clientHeight + 2 && b.clientHeight > 40)(document.querySelector('.title-input'))"))
    box.click(); page.keyboard.press('Control+End'); page.keyboard.type(' day'); page.keyboard.press('Enter'); page.wait_for_timeout(100)
    check('typing in the title saves, Enter finishes it', saved(page)['draft']['title'] == 'Upper body power and conditioning day' and page.evaluate("document.activeElement.className") != 'title-input')
    page.click('text=Tear out this page'); page.click('text=Tap again to throw it away')
    # stickers move as a layer, then settle
    tab(page, 'cover')
    g = page.locator('.sticker[aria-label="Hanging Gloves sticker"]'); b0 = g.bounding_box()
    page.mouse.move(b0['x'] + 30, b0['y'] + 30); page.mouse.down(); page.mouse.move(b0['x'] + 90, b0['y'] + 80, steps=5)
    mid = page.evaluate("(s => [s.style.translate, s.style.left])(document.querySelector('.sticker[aria-label=\"Hanging Gloves sticker\"]'))")
    page.mouse.up()
    after = page.evaluate("(s => s.style.translate)(document.querySelector('.sticker[aria-label=\"Hanging Gloves sticker\"]'))")
    check('a held sticker slides as a layer and lands in place', mid[0] != '' and after == '' and abs(g.bounding_box()['x'] - b0['x'] - 60) < 6, f"{mid} {after}")
    check('round 7 fixes: no console errors', not errors, '; '.join(errors[:4]))
    ctx.close()

    ctx, page, errors = open_app(browser)
    page.evaluate(STATS); page.reload(); page.wait_for_selector('.page')
    tab(page, 'stats'); page.click('.standards-row .chip:text-is("Men")'); page.wait_for_selector('.level')
    check('stats no longer has its own log form', page.locator('text=+ Log a max').count() == 0)
    page.click('.b3-row >> nth=0'); settle(page, 'lift')
    check('the squat page has the log-a-max button, and back goes to Stats', page.locator('text=+ Log a max').count() == 1 and page.get_attribute('a[href="#stats"]', 'href') == '#stats')
    page.click('text=+ Log a max'); page.wait_for_selector('.log-max:not([hidden])')
    page.fill('.log-max .calc-in >> nth=0', '405'); page.click('text=Save the max'); page.wait_for_timeout(300)
    m = saved(page)['maxes']
    check('a tested max is logged straight in, no page needed', len(m) == 1 and m[0]['liftId'] == 'squat' and m[0]['w'] == 405 and m[0]['unit'] == 'lb' and len(saved(page)['pages']) == 4, str(m))
    check('it is called a record', toast(page).startswith('New record: Squat 405 lb'), toast(page))
    page.click('text=Back to Stats'); settle(page, 'stats')
    row = page.locator('.b3-row >> nth=0').inner_text()
    check('the squat shows the tested 405', '405' in row and 'TESTED' in row.upper(), row[:80])
    check('the total counts it as lifted: 405 + 225 + 405', '1035' in page.inner_text('.b3-total'))
    page.click('.b3-row >> nth=0'); settle(page, 'lift')
    check('the lift history lists logged maxes', 'MAXES LOGGED' in page.inner_text('.page').upper() and 'TESTED MAX' in page.inner_text('.totals').upper())
    page.locator('.lift-remove').first.click(); page.locator('text=Tap again').first.click(); page.wait_for_timeout(200)
    check('a logged max can be removed', saved(page)['maxes'] == [])
    go(page, 'notebook'); page.click('text=The lift library'); settle(page, 'library'); page.fill('.search', 'Dumbbell Fly'); page.click('.pick >> nth=0'); settle(page, 'lift')
    check('other lifts get no estimated max', 'ESTIMATED' not in page.inner_text('.page').upper() and 'HEAVIEST LIFTED' in page.inner_text('.page').upper() and 'BEST SET' in page.inner_text('.page').upper())
    check('tested maxes: no console errors', not errors, '; '.join(errors[:4]))
    ctx.close()

    ctx, page, errors = open_app(browser)
    page.evaluate(STATS); page.reload(); page.wait_for_selector('.page')
    tab(page, 'more'); page.click('.seg button:text-is("kg")')
    check('kg is saved', saved(page)['settings']['units'] == 'kg')
    tab(page, 'stats')
    check('stats show in kg: 263 lb is 119.5 kg', '119.5' in page.locator('.b3-row >> nth=1').inner_text() and ' kg' in page.inner_text('.b3-total'), page.locator('.b3-row >> nth=1').inner_text()[:60])
    tab(page, 'today'); page.click('.repeat:has-text("Leg day")'); page.wait_for_selector('.title-input')
    check('a new page is written in kg', saved(page)['draft']['unit'] == 'kg' and 'KG' in page.inner_text('.set-cols').upper())
    check('last time is converted: 335 lb is 152.5 kg', page.locator('.set-row input').nth(0).get_attribute('placeholder') == '152.5')
    check('plates are in kilos', 'KG' in page.inner_text('.plates').upper() and '20' in page.inner_text('.plates'))
    go(page, 'notebook'); page.click('.filed-row >> nth=0'); settle(page, 'page')
    check('old pages keep their pounds', 'lb' in page.inner_text('.page') or '335' in page.inner_text('.page'))
    tab(page, 'more'); page.click('.seg button:text-is("Dim garage")')
    check('the dim garage switches on and is saved', page.evaluate("document.documentElement.dataset.look") == 'garage' and saved(page)['settings']['look'] == 'garage')
    paper = page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--paper').trim()")
    check('the paper turns gunmetal grey', paper.lower() == '#33363b', paper)
    cover = page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--blue').trim()")
    check('and the baby blue turns maroon', cover.lower() == '#5c1a27', cover)
    page.reload(); page.wait_for_selector('.page')
    check('it stays on after a reload', page.evaluate("document.documentElement.dataset.look") == 'garage')
    page.click('.seg button:text-is("Paper")')
    check('and switches back', page.evaluate("document.documentElement.dataset.look") == 'paper')
    check('units and look: no console errors', not errors, '; '.join(errors[:4]))
    ctx.close()

    # ---------- offline ----------
    import re as _re
    sw = open(os.path.join(REPO, 'sw.js')).read()
    listed = set(_re.findall(r"'\./(art/[^']+)'", sw))
    on_disk = set()
    for root, _, files in os.walk(os.path.join(REPO, 'art')):
        for f in files: on_disk.add(os.path.relpath(os.path.join(root, f), REPO))
    check('every drawing is on the offline list', on_disk <= listed, str(sorted(on_disk - listed)))
    if '_local' not in BASE:  # the single-file preview has no offline copy
        ctx = browser.new_context(viewport={'width': 390, 'height': 844})
        page = ctx.new_page(); errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(BASE); page.wait_for_selector('.page')
        page.evaluate("navigator.serviceWorker.ready"); page.wait_for_timeout(5000)
        saved_n = page.evaluate("caches.open('composition-v1').then(c => c.keys()).then(k => k.length)")
        check('the offline copy saves the app after one visit', saved_n > 40, str(saved_n))
        ctx.set_offline(True)
        page.reload(); page.wait_for_selector('.page', timeout=8000)
        page.click('.tab[data-tab=today]'); page.wait_for_timeout(500)
        page.click('.chip >> nth=0'); page.wait_for_selector('.title-input', timeout=5000)
        page.click('.tab[data-tab=stats]'); page.wait_for_timeout(600)
        broken = page.evaluate("[...document.images].filter(i => !i.complete || !i.naturalWidth).map(i => i.src)")
        check('with no signal it opens, starts a page and shows Stats with its art', page.locator('.b3-row').count() == 3 and not broken, str(broken))
        check('offline: no script errors', not errors, '; '.join(errors[:4]))
        ctx.close()

    # ---------- muscle map art ----------
    import xml.dom.minidom as _xml
    MAP_PARTS = {
        'traps': ['traps-upper', 'traps-middle', 'traps-lower'], 'front-delts': ['front-delts'],
        'side-delts': ['side-delts'], 'rear-delts': ['rear-delts'],
        'chest': ['chest-upper', 'chest-middle', 'chest-lower'],
        'biceps': ['biceps-long', 'biceps-short', 'brachialis'],
        'triceps': ['triceps-long', 'triceps-lateral', 'triceps-medial'],
        'forearms': ['brachioradialis', 'wrist-flexors', 'wrist-extensors'],
        'upper-back': ['rhomboids', 'infraspinatus', 'teres-minor', 'teres-major'],
        'lats': ['lats'], 'lower-back': ['lower-back'], 'abs': ['abs'],
        'obliques': ['external-oblique', 'serratus'], 'glutes': ['glute-max', 'glute-med'],
        'quads': ['rectus-femoris', 'vastus-lateralis', 'vastus-medialis', 'sartorius', 'tfl', 'hip-flexors'],
        'hamstrings': ['biceps-femoris', 'semitendinosus', 'semimembranosus'],
        'adductors': ['adductor-longus', 'adductor-magnus', 'gracilis', 'pectineus'],
        'calves': ['gastroc-medial', 'gastroc-lateral', 'soleus'], 'shins': ['tibialis-anterior']}
    part_group = {pt: g for g, pts in MAP_PARTS.items() for pt in pts}
    seen = {}
    for view in ('front', 'back'):
        path = os.path.join(REPO, 'art', f'muscle-{view}.svg')
        svg = open(path).read()
        try:
            _xml.parseString(svg); ok = True
        except Exception as e:
            ok = False
        check(f'muscle map {view}: the drawing is well formed', ok)
        shapes = _re.findall(r'<path class="mm-muscle" data-group="([^"]+)" data-part="([^"]+)"', svg)
        wrong = [(g, pt) for g, pt in shapes if part_group.get(pt) != g]
        check(f'muscle map {view}: every shape names a known part in the right group', shapes and not wrong, str(wrong[:4]))
        for g, pt in shapes: seen.setdefault(pt, set()).add(view)
        check(f'muscle map {view}: only the muscle shapes take taps',
              '.mm-ink,.mm-tone,.mm-gloss{pointer-events:none}' in svg)
        # every part can actually be tapped: some point inside it reaches it
        ctx = browser.new_context(viewport={'width': 390, 'height': 700}, device_scale_factor=2)
        page = ctx.new_page()
        page.set_content(f"<html><body style='margin:0'><style>svg{{width:380px}}</style>{svg}</body></html>")
        missed = page.evaluate("""() => {
          const out = [];
          const svg = document.querySelector('svg');
          const done = new Set();
          for (const el of document.querySelectorAll('.mm-muscle')) {
            const key = el.dataset.part;
            if (done.has(key)) continue;
            const b = el.getBBox(), m = el.getScreenCTM();
            let hit = false;
            for (let i = 1; i < 12 && !hit; i++) for (let j = 1; j < 12 && !hit; j++) {
              const p = svg.createSVGPoint(); p.x = b.x + b.width * i / 12; p.y = b.y + b.height * j / 12;
              if (!el.isPointInFill(p)) continue;
              const s = p.matrixTransform(m);
              const at = document.elementFromPoint(s.x, s.y);
              if (at && at.dataset && at.dataset.part === key) hit = true;
            }
            if (hit) done.add(key);
          }
          for (const el of document.querySelectorAll('.mm-muscle')) if (!done.has(el.dataset.part)) out.push(el.dataset.part);
          return [...new Set(out)];
        }""")
        check(f'muscle map {view}: every part can be tapped', not missed, str(missed))
        # muscle shapes do not overlap: paint each and count shared pixels
        over = page.evaluate("""() => {
          const els = [...document.querySelectorAll('.mm-muscle')];
          const W = 560, H = 860, cv = document.createElement('canvas'); cv.width = W; cv.height = H;
          const c = cv.getContext('2d'); const count = new Uint8Array(W * H);
          for (const el of els) {
            c.clearRect(0, 0, W, H); c.fill(new Path2D(el.getAttribute('d')));
            const px = c.getImageData(0, 0, W, H).data;
            for (let i = 0; i < W * H; i++) if (px[i * 4 + 3] > 200) count[i]++;
          }
          let inside = 0, shared = 0;
          for (const n of count) { if (n) inside++; if (n > 1) shared++; }
          return [shared, inside];
        }""")
        check(f'muscle map {view}: no two muscles overlap', over[0] <= over[1] * 0.002, f'{over[0]} of {over[1]} pixels shared')
        ctx.close()
    missing = [pt for pt in part_group if pt not in seen]
    check('muscle map: all 19 groups and every part are drawn', not missing and len(MAP_PARTS) == 19, str(missing))

    # ---------- muscle map content ----------
    import subprocess as _sp
    probe = r'''
      const M = await import(process.argv[1] + '/app/muscles.js');
      const { LIFTS } = await import(process.argv[1] + '/content/lifts.js');
      const by = id => LIFTS.find(l => l.id === id);
      const fs = await import('node:fs');
      const out = {
        groups: M.GROUPS.map(g => g.id), parts: M.PARTS.map(p => [p.id, p.group, p.view]),
        empty: M.PARTS.filter(p => !p.name || !p.does || !p.fact).map(p => p.id),
        long: M.PARTS.filter(p => [p.does, p.fact].some(t => (t.match(/[.!?](\s|$)/g) || []).length > 2)).map(p => p.id),
        unknown: M.unknownNames(LIFTS),
        pickUnknown: M.PICK.filter(n => !M.knowsName(n)),
        untrained: M.PARTS.filter(p => { const r = M.liftsFor(p.id, LIFTS); return !r.main.length && !r.help.length; }).map(p => p.id),
        bench: M.partsFor(by('bench-press')), incline: M.partsFor(by('incline-bench-press')),
        curl: M.partsFor(by('barbell-curl')), squat: M.partsFor(by('squat')),
        hammer: M.liftsFor('brachialis', LIFTS).main.map(l => l.id),
        dashes: /[\u2014\u2013]/.test(fs.readFileSync(process.argv[1] + '/content/muscles.js', 'utf8')),
      };
      console.log(JSON.stringify(out));
    '''
    r = _sp.run(['node', '--input-type=module', '-e', probe, REPO], capture_output=True, text=True)
    mc = json.loads(r.stdout) if r.returncode == 0 else None
    check('muscle content: the list loads', mc is not None, r.stderr[-300:])
    if mc:
        check('muscle content: 19 groups and 46 parts, each in a known group', len(mc['groups']) == 19 and len(mc['parts']) == 46 and len({p[0] for p in mc['parts']}) == 46 and all(p[1] in mc['groups'] for p in mc['parts']) and {p[1] for p in mc['parts']} == set(mc['groups']))
        drawn = {}
        for view in ('front', 'back'):
            for g, pt in _re.findall(r'<path class="mm-muscle" data-group="([^"]+)" data-part="([^"]+)"', open(os.path.join(REPO, 'art', f'muscle-{view}.svg')).read()):
                drawn.setdefault(pt, [g, set()])[1].add(view)
        off = [p for p in mc['parts'] if p[0] not in drawn or drawn[p[0]][0] != p[1] or drawn[p[0]][1] != ({'front', 'back'} if p[2] == 'both' else {p[2]})]
        check('muscle content: every part matches the drawings, group and view', not off and set(drawn) == {p[0] for p in mc['parts']}, str(off[:4]))
        check('muscle content: every part has a name, what it does and a fun fact', not mc['empty'], str(mc['empty']))
        check('muscle content: each line is one or two sentences', not mc['long'], str(mc['long']))
        check('muscle content: no em or en dashes', not mc['dashes'])
        check('muscle content: every muscle name in the lift list counts toward the map', not mc['unknown'], str(mc['unknown']))
        check('muscle content: every muscle you can pick for your own lift counts too', not mc['pickUnknown'], str(mc['pickUnknown']))
        check('muscle content: every part is trained by some lift in the library', not mc['untrained'], str(mc['untrained']))
        check('folding: bench works all of the chest, helped by front delts and triceps', sorted(mc['bench']['works']) == ['chest-lower', 'chest-middle', 'chest-upper'] and sorted(mc['bench']['helps']) == ['front-delts', 'triceps-lateral', 'triceps-long', 'triceps-medial'], str(mc['bench']))
        check('folding: incline bench works the upper chest only', mc['incline']['works'] == ['chest-upper'], str(mc['incline']))
        check('folding: "biceps" is the two heads, brachialis on its own', mc['curl'] == {'works': ['biceps-long', 'biceps-short'], 'helps': ['brachialis', 'brachioradialis', 'wrist-flexors', 'wrist-extensors']}, str(mc['curl']))
        check('folding: "quads" is the big three, not the hip flexors', set(mc['squat']['works']) == {'rectus-femoris', 'vastus-lateralis', 'vastus-medialis', 'glute-max', 'glute-med'}, str(mc['squat']))
        check('folding: hammer curls train the brachialis as a main muscle', 'hammer-curl' in mc['hammer'], str(mc['hammer']))

    # ---------- reduced motion and keyboard ----------
    ctx, page, errors = open_app(browser, reduced_motion='reduce')
    tab(page, 'today'); check('reduced motion: no flip, page still changes', page.locator('.sheet').count() == 0)
    tab(page, 'cover'); check('reduced motion: no console errors', not errors)
    ctx.close()
    ctx, page, errors = open_app(browser, 1280, 800)
    page.evaluate(SEED); page.reload(); page.wait_for_selector('.page')
    page.focus('.tab[data-tab=today]'); page.keyboard.press('Enter'); settle(page, 'today')
    page.focus('.repeat'); page.keyboard.press('Enter'); page.wait_for_selector('.title-input')
    page.focus('.set-row input'); page.keyboard.type('200'); page.keyboard.press('Tab'); page.keyboard.type('3'); page.keyboard.press('Tab'); page.keyboard.press('Tab'); page.keyboard.press('Space')
    s = saved(page)['draft']['lifts'][0]['sets'][0]
    check('keyboard: type, tab and space log a set', s['w'] == '200' and s['r'] == '3' and s['done'] is True, str(s))
    ctx.close()
    browser.close()

fails = [r for r in results if not r[1]]
print(f"\n{len(results) - len(fails)} passed, {len(fails)} failed")
sys.exit(1 if fails else 0)
