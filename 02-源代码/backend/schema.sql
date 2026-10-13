--
-- PostgreSQL database dump
--

\restrict vgqJwJZj5Efn6UTChDc3b4OAmHS6cgJFnHCUihamQmZQJJaaObX4WfMF3KzUYNM

-- Dumped from database version 18.4
-- Dumped by pg_dump version 18.4

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: audit; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audit (
    id integer NOT NULL,
    actor_id integer,
    action character varying(80) NOT NULL,
    detail character varying(300) NOT NULL,
    created_at timestamp with time zone
);


--
-- Name: audit_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.audit_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: audit_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.audit_id_seq OWNED BY public.audit.id;


--
-- Name: choice; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.choice (
    id integer NOT NULL,
    schedule_id integer NOT NULL,
    offering_id integer NOT NULL,
    kind character varying(20) NOT NULL,
    rank integer NOT NULL,
    status character varying(20) NOT NULL,
    CONSTRAINT choice_kind_check CHECK (((kind)::text = ANY ((ARRAY['primary'::character varying, 'alternate'::character varying])::text[]))),
    CONSTRAINT choice_status_check CHECK (((status)::text = ANY ((ARRAY['selected'::character varying, 'enrolled'::character varying, 'cancelled'::character varying])::text[])))
);


--
-- Name: choice_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.choice_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: choice_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.choice_id_seq OWNED BY public.choice.id;


--
-- Name: course; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.course (
    id integer NOT NULL,
    code character varying(20) NOT NULL,
    name character varying(80) NOT NULL,
    department character varying(80) NOT NULL,
    credits integer NOT NULL,
    fee_cents integer NOT NULL,
    prerequisite_id integer
);


--
-- Name: course_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.course_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: course_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.course_id_seq OWNED BY public.course.id;


--
-- Name: eligibility; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.eligibility (
    professor_id integer NOT NULL,
    course_id integer NOT NULL
);


--
-- Name: grade; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.grade (
    student_id integer NOT NULL,
    offering_id integer NOT NULL,
    value character varying(1) NOT NULL,
    CONSTRAINT grade_value_check CHECK (((value)::text = ANY ((ARRAY['A'::character varying, 'B'::character varying, 'C'::character varying, 'D'::character varying, 'F'::character varying, 'I'::character varying])::text[])))
);


--
-- Name: invoice; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.invoice (
    id integer NOT NULL,
    student_id integer NOT NULL,
    term_id integer NOT NULL,
    amount_cents integer NOT NULL,
    payload json NOT NULL,
    status character varying(20) NOT NULL,
    attempts integer NOT NULL,
    last_error character varying(200),
    next_attempt timestamp with time zone
);


--
-- Name: invoice_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.invoice_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: invoice_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.invoice_id_seq OWNED BY public.invoice.id;


--
-- Name: offering; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.offering (
    id integer NOT NULL,
    course_id integer NOT NULL,
    term_id integer NOT NULL,
    professor_id integer,
    day integer NOT NULL,
    start integer NOT NULL,
    "end" integer NOT NULL,
    room character varying(40) NOT NULL,
    status character varying(20) NOT NULL,
    CONSTRAINT offering_check CHECK (((start >= 1) AND ("end" >= start) AND ("end" <= 12))),
    CONSTRAINT offering_day_check CHECK (((day >= 1) AND (day <= 7))),
    CONSTRAINT offering_status_check CHECK (((status)::text = ANY ((ARRAY['open'::character varying, 'closed'::character varying, 'cancelled'::character varying])::text[])))
);


--
-- Name: offering_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.offering_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: offering_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.offering_id_seq OWNED BY public.offering.id;


--
-- Name: schedule; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.schedule (
    id integer NOT NULL,
    student_id integer NOT NULL,
    term_id integer NOT NULL,
    submitted boolean NOT NULL
);


--
-- Name: schedule_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.schedule_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: schedule_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.schedule_id_seq OWNED BY public.schedule.id;


--
-- Name: term; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.term (
    id integer NOT NULL,
    name character varying(40) NOT NULL,
    state character varying(20) NOT NULL,
    current boolean NOT NULL,
    CONSTRAINT term_state_check CHECK (((state)::text = ANY ((ARRAY['open'::character varying, 'closed'::character varying])::text[])))
);


--
-- Name: term_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.term_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: term_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.term_id_seq OWNED BY public.term.id;


--
-- Name: user; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."user" (
    id integer NOT NULL,
    username character varying(50) NOT NULL,
    password_hash character varying(256) NOT NULL,
    role character varying(20) NOT NULL,
    name character varying(80) NOT NULL,
    department character varying(80),
    birth_date character varying(10),
    graduation_date character varying(10),
    identity_number character varying(30),
    status character varying(20) NOT NULL,
    CONSTRAINT user_role_check CHECK (((role)::text = ANY ((ARRAY['student'::character varying, 'professor'::character varying, 'registrar'::character varying])::text[]))),
    CONSTRAINT user_status_check CHECK (((status)::text = ANY ((ARRAY['active'::character varying, 'inactive'::character varying, 'deleted'::character varying])::text[])))
);


--
-- Name: user_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_id_seq OWNED BY public."user".id;


--
-- Name: audit id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit ALTER COLUMN id SET DEFAULT nextval('public.audit_id_seq'::regclass);


--
-- Name: choice id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.choice ALTER COLUMN id SET DEFAULT nextval('public.choice_id_seq'::regclass);


--
-- Name: course id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.course ALTER COLUMN id SET DEFAULT nextval('public.course_id_seq'::regclass);


--
-- Name: invoice id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.invoice ALTER COLUMN id SET DEFAULT nextval('public.invoice_id_seq'::regclass);


--
-- Name: offering id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.offering ALTER COLUMN id SET DEFAULT nextval('public.offering_id_seq'::regclass);


--
-- Name: schedule id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schedule ALTER COLUMN id SET DEFAULT nextval('public.schedule_id_seq'::regclass);


--
-- Name: term id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.term ALTER COLUMN id SET DEFAULT nextval('public.term_id_seq'::regclass);


--
-- Name: user id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."user" ALTER COLUMN id SET DEFAULT nextval('public.user_id_seq'::regclass);


--
-- Name: audit audit_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit
    ADD CONSTRAINT audit_pkey PRIMARY KEY (id);


--
-- Name: choice choice_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.choice
    ADD CONSTRAINT choice_pkey PRIMARY KEY (id);


--
-- Name: choice choice_schedule_id_offering_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.choice
    ADD CONSTRAINT choice_schedule_id_offering_id_key UNIQUE (schedule_id, offering_id);


--
-- Name: course course_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.course
    ADD CONSTRAINT course_code_key UNIQUE (code);


--
-- Name: course course_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.course
    ADD CONSTRAINT course_pkey PRIMARY KEY (id);


--
-- Name: eligibility eligibility_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.eligibility
    ADD CONSTRAINT eligibility_pkey PRIMARY KEY (professor_id, course_id);


--
-- Name: grade grade_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.grade
    ADD CONSTRAINT grade_pkey PRIMARY KEY (student_id, offering_id);


--
-- Name: invoice invoice_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.invoice
    ADD CONSTRAINT invoice_pkey PRIMARY KEY (id);


--
-- Name: invoice invoice_student_id_term_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.invoice
    ADD CONSTRAINT invoice_student_id_term_id_key UNIQUE (student_id, term_id);


--
-- Name: offering offering_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.offering
    ADD CONSTRAINT offering_pkey PRIMARY KEY (id);


--
-- Name: schedule schedule_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schedule
    ADD CONSTRAINT schedule_pkey PRIMARY KEY (id);


--
-- Name: schedule schedule_student_id_term_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schedule
    ADD CONSTRAINT schedule_student_id_term_id_key UNIQUE (student_id, term_id);


--
-- Name: term term_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.term
    ADD CONSTRAINT term_pkey PRIMARY KEY (id);


--
-- Name: user user_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);


--
-- Name: user user_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_username_key UNIQUE (username);


--
-- Name: audit audit_actor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit
    ADD CONSTRAINT audit_actor_id_fkey FOREIGN KEY (actor_id) REFERENCES public."user"(id);


--
-- Name: choice choice_offering_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.choice
    ADD CONSTRAINT choice_offering_id_fkey FOREIGN KEY (offering_id) REFERENCES public.offering(id);


--
-- Name: choice choice_schedule_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.choice
    ADD CONSTRAINT choice_schedule_id_fkey FOREIGN KEY (schedule_id) REFERENCES public.schedule(id) ON DELETE CASCADE;


--
-- Name: course course_prerequisite_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.course
    ADD CONSTRAINT course_prerequisite_id_fkey FOREIGN KEY (prerequisite_id) REFERENCES public.course(id);


--
-- Name: eligibility eligibility_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.eligibility
    ADD CONSTRAINT eligibility_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.course(id);


--
-- Name: eligibility eligibility_professor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.eligibility
    ADD CONSTRAINT eligibility_professor_id_fkey FOREIGN KEY (professor_id) REFERENCES public."user"(id);


--
-- Name: grade grade_offering_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.grade
    ADD CONSTRAINT grade_offering_id_fkey FOREIGN KEY (offering_id) REFERENCES public.offering(id);


--
-- Name: grade grade_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.grade
    ADD CONSTRAINT grade_student_id_fkey FOREIGN KEY (student_id) REFERENCES public."user"(id);


--
-- Name: invoice invoice_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.invoice
    ADD CONSTRAINT invoice_student_id_fkey FOREIGN KEY (student_id) REFERENCES public."user"(id);


--
-- Name: invoice invoice_term_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.invoice
    ADD CONSTRAINT invoice_term_id_fkey FOREIGN KEY (term_id) REFERENCES public.term(id);


--
-- Name: offering offering_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.offering
    ADD CONSTRAINT offering_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.course(id);


--
-- Name: offering offering_professor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.offering
    ADD CONSTRAINT offering_professor_id_fkey FOREIGN KEY (professor_id) REFERENCES public."user"(id);


--
-- Name: offering offering_term_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.offering
    ADD CONSTRAINT offering_term_id_fkey FOREIGN KEY (term_id) REFERENCES public.term(id);


--
-- Name: schedule schedule_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schedule
    ADD CONSTRAINT schedule_student_id_fkey FOREIGN KEY (student_id) REFERENCES public."user"(id);


--
-- Name: schedule schedule_term_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schedule
    ADD CONSTRAINT schedule_term_id_fkey FOREIGN KEY (term_id) REFERENCES public.term(id);


--
-- PostgreSQL database dump complete
--

\unrestrict vgqJwJZj5Efn6UTChDc3b4OAmHS6cgJFnHCUihamQmZQJJaaObX4WfMF3KzUYNM

