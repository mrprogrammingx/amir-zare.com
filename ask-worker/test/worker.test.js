import { test } from "node:test";
import assert from "node:assert/strict";
import { handle, validateAnswer } from "../src/index.js";

const KB = [
  { id: "profile", title: "Profile", url: "https://amir-zare.com/about/", sentences: [
    "Amir's job title is AI and Data Engineer.",
    "Amir currently works as Founder / AI & Data Engineer at DataLayer (since Jan 2024)." ] },
  { id: "languages", title: "Languages", url: "https://amir-zare.com/resume.html", sentences: [
    "Amir speaks English (Full Professional)." ] },
];
globalThis.fetch = async () => new Response(JSON.stringify(KB), { status: 200 });

const ORIGIN = "https://amir-zare.com";
const env = (reply, opts = {}) => {
  const e = { AI: { run: async (model, input) => {
    if (opts.fail && opts.fail.includes(model)) throw new Error("quota exceeded");
    e.last = { model, input };
    return typeof reply === "function" ? reply(model, input) : reply;
  } } };
  return e;
};
const req = (body, origin = ORIGIN, method = "POST", ip = String(Math.random())) => new Request("https://amir-zare.com/api/ask", {
  method, headers: { "Content-Type": "application/json", Origin: origin, "CF-Connecting-IP": ip },
  body: method === "POST" ? JSON.stringify(body) : undefined });
const call = async (body, e, ...rest) => { const r = await handle(req(body, ...rest), e, {}); return { r, j: await r.json().catch(() => null) }; };

test("answers with validated, renumbered citations and CORS", async () => {
  const e = env({ response: "Amir is an AI and Data Engineer [1] and founder of DataLayer [2]." });
  const { r, j } = await call({ question: "What is his job?", ids: ["profile#0", "profile#1", "languages#0"] }, e);
  assert.equal(r.status, 200); assert.equal(j.status, "answer");
  assert.match(j.answer, /\[1\].*\[2\]/); assert.equal(j.citations.length, 2);
  assert.equal(j.citations[1].text, KB[0].sentences[1]);
  assert.equal(r.headers.get("Access-Control-Allow-Origin"), ORIGIN);
  assert.match(e.last.input.messages[1].content, /\[1\] Amir's job title/);
});
test("drops citations to facts that weren't provided; no valid citation => no_answer", async () => {
  assert.equal(validateAnswer("Amir knows Rust [7].", [{ text: "x" }]), null);
  const v = validateAnswer("A [2] and B [9].", [{ text: "a" }, { text: "b" }]);
  assert.equal(v.answer, "A [1] and B."); assert.equal(v.citations.length, 1);
});
test("NO_ANSWER from the model => no_answer", async () => {
  const { j } = await call({ question: "Does he know Rust?", ids: ["profile#0"] }, env({ response: "NO_ANSWER" }));
  assert.equal(j.status, "no_answer");
});
test("OpenAI-style output shape is understood", async () => {
  const { j } = await call({ question: "Job?", ids: ["profile#0"] }, env({ choices: [{ message: { content: "AI and Data Engineer [1]." } }] }));
  assert.equal(j.status, "answer");
});
test("falls back to the second model, then reports unavailable", async () => {
  const e = env({ response: "Founder [1]." }, { fail: ["@cf/meta/llama-3.3-70b-instruct-fp8-fast"] });
  const { j } = await call({ question: "Job?", ids: ["profile#1"] }, e);
  assert.equal(j.status, "answer"); assert.equal(j.model, "@cf/zai-org/glm-4.7-flash");
  const e2 = env({}, { fail: ["@cf/meta/llama-3.3-70b-instruct-fp8-fast", "@cf/zai-org/glm-4.7-flash"] });
  const { r, j: j2 } = await call({ question: "Job?", ids: ["profile#1"] }, e2);
  assert.equal(r.status, 503); assert.equal(j2.status, "unavailable");
});
test("guard, unknown ids, other origins and bad input", async () => {
  const e = env({ response: "x [1]" });
  assert.equal((await call({ question: "What is his salary?", ids: ["profile#0"] }, e)).j.status, "guard");
  assert.equal((await call({ question: "Job?", ids: ["made-up#1"] }, e)).j.status, "no_answer");
  assert.equal((await call({ question: "Job?", ids: ["profile#0"] }, e, "https://evil.example")).r.status, 403);
  assert.equal((await call({ question: "x".repeat(400), ids: ["profile#0"] }, e)).r.status, 400);
  const pre = await handle(req(null, ORIGIN, "OPTIONS"), e, {});
  assert.equal(pre.status, 204); assert.equal(pre.headers.get("Access-Control-Allow-Methods"), "POST, OPTIONS");
});
test("per-IP limit kicks in after 6 questions a minute", async () => {
  const e = env({ response: "x [1]" }); let last;
  for (let i = 0; i < 7; i++) last = await handle(req({ question: "Job?", ids: ["profile#0"] }, ORIGIN, "POST", "1.2.3.4"), e, {});
  assert.equal(last.status, 429);
});

// ------------------------------------------------------------------ fixes from the review
const facts2 = [{ text: "Amir's job title is AI and Data Engineer." }, { text: "Amir founded DataLayer." }];

test("uncited sentences are dropped, cited ones kept (Rust/Google example)", () => {
  const v = validateAnswer("Amir is an AI and Data Engineer [1]. He has 15 years of Rust experience at Google.", facts2);
  assert.equal(v.answer, "Amir is an AI and Data Engineer [1].");
  assert.doesNotMatch(v.answer, /Rust|Google/);
  assert.equal(v.citations.length, 1);
  // only uncited sentences left => no_answer
  assert.equal(validateAnswer("He has 15 years of Rust experience at Google.", facts2), null);
  // a sentence whose only citation points to a fact that wasn't provided is dropped too
  assert.equal(validateAnswer("Amir founded DataLayer [2]. He knows Rust [9].", facts2).answer, "Amir founded DataLayer [1].");
});

test("other citation styles are understood", () => {
  for (const raw of ["Amir is an engineer [1, 2].", "Amir is an engineer [1][2].", "Amir is an engineer (1, 2).", "Amir is an engineer [^1][^2].", "Amir is an engineer. [1] [2]"]) {
    const v = validateAnswer(raw, facts2);
    assert.ok(v, raw); assert.equal(v.answer, "Amir is an engineer [1][2].", raw); assert.equal(v.citations.length, 2, raw);
  }
  // dotted names don't split sentences
  assert.equal(validateAnswer("Amir built it with Next.js and Node.js [2].", facts2).answer, "Amir built it with Next.js and Node.js [1].");
});

test("a JSON body that isn't an object is a bad request, not a crash", async () => {
  for (const body of ["null", "[]", "42", '"text"']) {
    const r = await handle(new Request("https://amir-zare.com/api/ask", { method: "POST", body,
      headers: { "Content-Type": "application/json", Origin: ORIGIN, "CF-Connecting-IP": String(Math.random()) } }), env({ response: "x [1]" }), {});
    assert.equal(r.status, 400, body); assert.equal((await r.json()).status, "bad_request", body);
  }
});

test("AI error details are not sent to the caller", async () => {
  const secret = "10000 neurons used for account 1234abcd";
  const e = { AI: { run: async () => { throw new Error(secret); } } };
  const errors = []; const orig = console.error; console.error = (...a) => errors.push(a.join(" "));
  try {
    const { r, j } = await call({ question: "Job?", ids: ["profile#0"] }, e);
    assert.equal(r.status, 503); assert.equal(j.status, "unavailable"); assert.equal(j.error, "AI unavailable");
    assert.ok(!JSON.stringify(j).includes("1234abcd"));
    assert.ok(errors.some((x) => x.includes("1234abcd")), "logged for the owner");
  } finally { console.error = orig; }
});

test("guard: technical questions pass, personal ones are refused", async () => {
  const e = env({ response: "Amir is an AI and Data Engineer [1]." });
  for (const q of ["Has he built a single-page app?", "Did he work on health checks or monitoring?", "Has he worked on a product family of APIs?",
    "Does he know Visa payment integrations?", "What is the average age of his data pipelines?", "Has he used child processes or kids-friendly apps?"]) {
    assert.equal((await call({ question: q, ids: ["profile#0"] }, e)).j.status, "answer", q);
  }
  for (const [q, reason] of [["How old is he?", "age"], ["Is he married?", "family life"], ["Does he need a visa?", "residency or immigration details"],
    ["What is his salary expectation?", "pay expectations"]]) {
    const { j } = await call({ question: q, ids: ["profile#0"] }, e);
    assert.equal(j.status, "guard", q); assert.equal(j.reason, reason, q);
  }
});

test("rate-limit binding is used as well as the per-instance limit, and a failing binding doesn't block", async () => {
  const e = env({ response: "x [1]" });
  e.RATE_LIMITER = { limit: async () => ({ success: false }) };
  assert.equal((await call({ question: "Job?", ids: ["profile#0"] }, e)).r.status, 429);
  e.RATE_LIMITER = { limit: async () => { throw new Error("binding down"); } };
  const orig = console.error; console.error = () => {};
  try { assert.equal((await call({ question: "Job?", ids: ["profile#0"] }, e)).r.status, 200); } finally { console.error = orig; }
});
