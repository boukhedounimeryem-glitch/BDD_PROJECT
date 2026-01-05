--
-- PostgreSQL database dump
--

-- Dumped from database version 17.7
-- Dumped by pg_dump version 17.7

-- Started on 2025-12-30 22:37:21

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

--
-- TOC entry 234 (class 1255 OID 41126)
-- Name: check_exam_overlap(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE OR REPLACE FUNCTION public.check_exam_overlap() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM examen e
        WHERE e.salle_id = NEW.salle_id
          AND e.date = NEW.date
          AND (
              NEW.heure_debut < e.heure_debut + (e.duree_minutes || ' minutes')::interval
          AND e.heure_debut < NEW.heure_debut + (NEW.duree_minutes || ' minutes')::interval
          )
          AND e.id <> NEW.id
    ) THEN
        RAISE EXCEPTION 'Chevauchement d''examens dans la même salle';
    END IF;

    RETURN NEW;
END;
$$;


ALTER FUNCTION public.check_exam_overlap() OWNER TO postgres;

--
-- TOC entry 233 (class 1255 OID 41124)
-- Name: check_professor_max_3_exams(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE OR REPLACE FUNCTION public.check_professor_max_3_exams() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF (
        SELECT COUNT(*)
        FROM examen
        WHERE professeur_id = NEW.professeur_id
        AND date = NEW.date
    ) >= 3 THEN
        RAISE EXCEPTION 'Un professeur ne peut pas surveiller plus de 3 examens par jour';
    END IF;

    RETURN NEW;
END;
$$;


ALTER FUNCTION public.check_professor_max_3_exams() OWNER TO postgres;

--
-- TOC entry 232 (class 1255 OID 41122)
-- Name: check_student_one_exam_per_day(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE OR REPLACE FUNCTION public.check_student_one_exam_per_day() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM inscription i
        JOIN examen e ON e.module_id = i.module_id
        WHERE i.etudiant_id IN (
            SELECT etudiant_id
            FROM inscription
            WHERE module_id = NEW.module_id
        )
        AND e.date = NEW.date
        AND e.id <> NEW.id
    ) THEN
        RAISE EXCEPTION 'Un étudiant ne peut pas avoir plus d''un examen par jour';
    END IF;

    RETURN NEW;
END;
$$;


ALTER FUNCTION public.check_student_one_exam_per_day() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 218 (class 1259 OID 41010)
-- Name: departement; Type: TABLE; Schema: public; Owner: postgres
--

DROP TABLE IF EXISTS public.departement CASCADE;
CREATE TABLE public.departement (
    id integer NOT NULL,
    nom character varying(100) NOT NULL
);


ALTER TABLE public.departement OWNER TO postgres;

--
-- TOC entry 217 (class 1259 OID 41009)
-- Name: departement_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.departement_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.departement_id_seq OWNER TO postgres;

--
-- TOC entry 4953 (class 0 OID 0)
-- Dependencies: 217
-- Name: departement_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.departement_id_seq OWNED BY public.departement.id;


--
-- TOC entry 224 (class 1259 OID 41044)
-- Name: etudiant; Type: TABLE; Schema: public; Owner: postgres
--

DROP TABLE IF EXISTS public.etudiant CASCADE;
CREATE TABLE public.etudiant (
    id integer NOT NULL,
    nom character varying(100) NOT NULL,
    prenom character varying(100) NOT NULL,
    promotion integer NOT NULL,
    formation_id integer NOT NULL
);


ALTER TABLE public.etudiant OWNER TO postgres;

--
-- TOC entry 223 (class 1259 OID 41043)
-- Name: etudiant_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.etudiant_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.etudiant_id_seq OWNER TO postgres;

--
-- TOC entry 4954 (class 0 OID 0)
-- Dependencies: 223
-- Name: etudiant_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.etudiant_id_seq OWNED BY public.etudiant.id;


--
-- TOC entry 230 (class 1259 OID 41083)
-- Name: examen; Type: TABLE; Schema: public; Owner: postgres
--

DROP TABLE IF EXISTS public.examen CASCADE;
CREATE TABLE public.examen (
    id integer NOT NULL,
    date date NOT NULL,
    heure_debut time without time zone NOT NULL,
    duree_minutes integer NOT NULL,
    module_id integer NOT NULL,
    professeur_id integer NOT NULL,
    salle_id integer NOT NULL,
    CONSTRAINT examen_duree_minutes_check CHECK ((duree_minutes > 0))
);


ALTER TABLE public.examen OWNER TO postgres;

--
-- TOC entry 229 (class 1259 OID 41082)
-- Name: examen_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.examen_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.examen_id_seq OWNER TO postgres;

--
-- TOC entry 4955 (class 0 OID 0)
-- Dependencies: 229
-- Name: examen_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.examen_id_seq OWNED BY public.examen.id;


--
-- TOC entry 220 (class 1259 OID 41019)
-- Name: formation; Type: TABLE; Schema: public; Owner: postgres
--

DROP TABLE IF EXISTS public.formation CASCADE;
CREATE TABLE public.formation (
    id integer NOT NULL,
    nom character varying(100) NOT NULL,
    niveau character varying(50) NOT NULL,
    nb_modules integer NOT NULL,
    departement_id integer NOT NULL,
    CONSTRAINT formation_nb_modules_check CHECK ((nb_modules > 0))
);


ALTER TABLE public.formation OWNER TO postgres;

--
-- TOC entry 219 (class 1259 OID 41018)
-- Name: formation_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.formation_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.formation_id_seq OWNER TO postgres;

--
-- TOC entry 4956 (class 0 OID 0)
-- Dependencies: 219
-- Name: formation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.formation_id_seq OWNED BY public.formation.id;


--
-- TOC entry 231 (class 1259 OID 41107)
-- Name: inscription; Type: TABLE; Schema: public; Owner: postgres
--

DROP TABLE IF EXISTS public.inscription CASCADE;
CREATE TABLE public.inscription (
    etudiant_id integer NOT NULL,
    module_id integer NOT NULL,
    note double precision
);


ALTER TABLE public.inscription OWNER TO postgres;

--
-- TOC entry 226 (class 1259 OID 41056)
-- Name: module; Type: TABLE; Schema: public; Owner: postgres
--

DROP TABLE IF EXISTS public.module CASCADE;
CREATE TABLE public.module (
    id integer NOT NULL,
    nom character varying(100) NOT NULL,
    credits integer NOT NULL,
    formation_id integer NOT NULL,
    pre_requis_id integer,
    CONSTRAINT module_credits_check CHECK ((credits > 0))
);


ALTER TABLE public.module OWNER TO postgres;

--
-- TOC entry 225 (class 1259 OID 41055)
-- Name: module_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.module_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.module_id_seq OWNER TO postgres;

--
-- TOC entry 4957 (class 0 OID 0)
-- Dependencies: 225
-- Name: module_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.module_id_seq OWNED BY public.module.id;


--
-- TOC entry 222 (class 1259 OID 41032)
-- Name: professeur; Type: TABLE; Schema: public; Owner: postgres
--

DROP TABLE IF EXISTS public.professeur CASCADE;
CREATE TABLE public.professeur (
    id integer NOT NULL,
    nom character varying(100) NOT NULL,
    specialite character varying(100),
    departement_id integer NOT NULL
);


ALTER TABLE public.professeur OWNER TO postgres;

--
-- TOC entry 221 (class 1259 OID 41031)
-- Name: professeur_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.professeur_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.professeur_id_seq OWNER TO postgres;

--
-- TOC entry 4958 (class 0 OID 0)
-- Dependencies: 221
-- Name: professeur_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.professeur_id_seq OWNED BY public.professeur.id;


--
-- TOC entry 228 (class 1259 OID 41074)
-- Name: salle; Type: TABLE; Schema: public; Owner: postgres
--

DROP TABLE IF EXISTS public.salle CASCADE;
CREATE TABLE public.salle (
    id integer NOT NULL,
    nom character varying(100) NOT NULL,
    capacite integer NOT NULL,
    type character varying(20) NOT NULL,
    batiment character varying(100) NOT NULL,
    CONSTRAINT salle_capacite_check CHECK ((capacite > 0)),
    CONSTRAINT salle_type_check CHECK (((type)::text = ANY ((ARRAY['amphi'::character varying, 'salle'::character varying])::text[])))
);


ALTER TABLE public.salle OWNER TO postgres;

--
-- TOC entry 227 (class 1259 OID 41073)
-- Name: salle_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.salle_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.salle_id_seq OWNER TO postgres;

--
-- TOC entry 4959 (class 0 OID 0)
-- Dependencies: 227
-- Name: salle_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.salle_id_seq OWNED BY public.salle.id;


--
-- TOC entry 4733 (class 2604 OID 41013)
-- Name: departement id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.departement ALTER COLUMN id SET DEFAULT nextval('public.departement_id_seq'::regclass);


--
-- TOC entry 4736 (class 2604 OID 41047)
-- Name: etudiant id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.etudiant ALTER COLUMN id SET DEFAULT nextval('public.etudiant_id_seq'::regclass);


--
-- TOC entry 4739 (class 2604 OID 41086)
-- Name: examen id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.examen ALTER COLUMN id SET DEFAULT nextval('public.examen_id_seq'::regclass);


--
-- TOC entry 4734 (class 2604 OID 41022)
-- Name: formation id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.formation ALTER COLUMN id SET DEFAULT nextval('public.formation_id_seq'::regclass);


--
-- TOC entry 4737 (class 2604 OID 41059)
-- Name: module id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.module ALTER COLUMN id SET DEFAULT nextval('public.module_id_seq'::regclass);


--
-- TOC entry 4735 (class 2604 OID 41035)
-- Name: professeur id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.professeur ALTER COLUMN id SET DEFAULT nextval('public.professeur_id_seq'::regclass);


--
-- TOC entry 4738 (class 2604 OID 41077)
-- Name: salle id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.salle ALTER COLUMN id SET DEFAULT nextval('public.salle_id_seq'::regclass);


--
-- TOC entry 4934 (class 0 OID 41010)
-- Dependencies: 218
-- Data for Name: departement; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.departement (id, nom) VALUES
(1, 'Informatique'),
(2, 'Mathématiques'),
(3, 'Physique'),
(4, 'Gestion');


--
-- TOC entry 4940 (class 0 OID 41044)
-- Dependencies: 224
-- Data for Name: etudiant; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.etudiant (id, nom, prenom, promotion, formation_id) VALUES
(1, 'Kaci', 'Amine', 2023, 3),
(2, 'Benali', 'Sara', 2023, 3),
(3, 'Toumi', 'Yanis', 2023, 6),
(4, 'El Idrissi', 'Salma', 2023, 3),
(5, 'Haddad', 'Rania', 2024, 4),
(6, 'Omar', 'Nabil', 2024, 7),
(7, 'Fouad', 'Lina', 2023, 8),
(8, 'Karim', 'Soufiane', 2023, 1),
(9, 'Jawad', 'Imane', 2022, 2),
(10, 'Said', 'Youssef', 2022, 9);


--
-- TOC entry 4946 (class 0 OID 41083)
-- Dependencies: 230
-- Data for Name: examen; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.examen (id, date, heure_debut, duree_minutes, module_id, professeur_id, salle_id) VALUES
(1, '2025-01-10', '09:00:00', 120, 6, 1, 1),
(2, '2025-01-10', '14:00:00', 120, 7, 2, 1),
(3, '2025-01-11', '09:00:00', 90, 8, 8, 2),
(4, '2025-01-11', '11:30:00', 90, 1, 4, 2),
(5, '2025-01-12', '09:00:00', 120, 2, 5, 1),
(6, '2025-01-12', '14:00:00', 120, 13, 6, 1),
(7, '2025-01-13', '09:00:00', 90, 14, 6, 2),
(8, '2025-01-13', '14:00:00', 90, 15, 7, 2);


--
-- TOC entry 4936 (class 0 OID 41019)
-- Dependencies: 220
-- Data for Name: formation; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.formation (id, nom, niveau, nb_modules, departement_id) VALUES
(1, 'Licence Informatique 1', 'L1', 5, 1),
(2, 'Licence Informatique 2', 'L2', 6, 1),
(3, 'Licence Informatique 3', 'L3', 6, 1),
(4, 'Master Informatique 1', 'M1', 5, 1),
(5, 'Master Informatique 2', 'M2', 4, 1),
(6, 'Licence Mathématiques 3', 'L3', 5, 2),
(7, 'Master Mathématiques 1', 'M1', 4, 2),
(8, 'Licence Physique 3', 'L3', 5, 3),
(9, 'Licence Gestion 3', 'L3', 5, 4);


--
-- TOC entry 4947 (class 0 OID 41107)
-- Dependencies: 231
-- Data for Name: inscription; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.inscription (etudiant_id, module_id, note) VALUES
-- Étudiants Licence Info 3
(1, 6, NULL),
(1, 7, NULL),
(1, 8, NULL),
(2, 6, NULL),
(2, 7, NULL),
(2, 10, NULL),
(4, 7, NULL),
(4, 8, NULL),
-- Étudiants Math
(3, 1, NULL),
(3, 2, NULL),
(6, 4, NULL),
(6, 5, NULL),
-- Étudiants Physique
(7, 13, NULL),
(7, 14, NULL),
-- Étudiants autres formations
(8, 6, NULL),
(9, 2, NULL),
(10, 15, NULL);


--
-- TOC entry 4942 (class 0 OID 41056)
-- Dependencies: 226
-- Data for Name: module; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.module (id, nom, credits, formation_id, pre_requis_id) VALUES
-- Mathématiques
(1, 'Algèbre 1', 6, 6, NULL),
(2, 'Analyse 1', 6, 6, NULL),
(3, 'Probabilités', 6, 6, NULL),
(4, 'Statistiques', 6, 7, NULL),
(5, 'Analyse avancée', 6, 7, 2),
-- Informatique Licence 3
(6, 'Programmation Python', 6, 3, NULL),
(7, 'Bases de données', 6, 3, NULL),
(8, 'Réseaux informatiques', 6, 3, NULL),
(9, 'Systèmes d''exploitation', 6, 3, NULL),
(10, 'Développement web', 6, 3, NULL),
-- Informatique Master
(11, 'Intelligence artificielle', 6, 4, 6),
(12, 'Big Data', 6, 4, 7),
-- Physique
(13, 'Mécanique quantique', 6, 8, NULL),
(14, 'Électromagnétisme', 6, 8, NULL),
-- Gestion
(15, 'Gestion de projet', 4, 9, NULL);


--
-- TOC entry 4938 (class 0 OID 41032)
-- Dependencies: 222
-- Data for Name: professeur; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.professeur (id, nom, specialite, departement_id) VALUES
(1, 'Dr Ait Ahmed', 'Bases de données', 1),
(2, 'Dr Benali', 'Intelligence artificielle', 1),
(3, 'Dr Cherif', 'Algorithmes', 1),
(4, 'Dr Dupont', 'Analyse', 2),
(5, 'Dr Martin', 'Probabilités et statistiques', 2),
(6, 'Dr Durand', 'Physique quantique', 3),
(7, 'Dr Leroy', 'Management', 4),
(8, 'Dr Moreau', 'Réseaux', 1);


--
-- TOC entry 4944 (class 0 OID 41074)
-- Dependencies: 228
-- Data for Name: salle; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.salle (id, nom, capacite, type, batiment) VALUES
(1, 'Amphi A', 300, 'amphi', 'Bloc A'),
(2, 'Salle B1', 30, 'salle', 'Bloc B');


--
-- TOC entry 4960 (class 0 OID 0)
-- Dependencies: 217
-- Name: departement_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.departement_id_seq', 3, true);


--
-- TOC entry 4961 (class 0 OID 0)
-- Dependencies: 223
-- Name: etudiant_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.etudiant_id_seq', 3, true);


--
-- TOC entry 4962 (class 0 OID 0)
-- Dependencies: 229
-- Name: examen_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.examen_id_seq', 4, true);


--
-- TOC entry 4963 (class 0 OID 0)
-- Dependencies: 219
-- Name: formation_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.formation_id_seq', 2, true);


--
-- TOC entry 4964 (class 0 OID 0)
-- Dependencies: 225
-- Name: module_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.module_id_seq', 3, true);


--
-- TOC entry 4965 (class 0 OID 0)
-- Dependencies: 221
-- Name: professeur_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.professeur_id_seq', 3, true);


--
-- TOC entry 4966 (class 0 OID 0)
-- Dependencies: 227
-- Name: salle_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.salle_id_seq', 2, true);


--
-- TOC entry 4746 (class 2606 OID 41017)
-- Name: departement departement_nom_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.departement
    ADD CONSTRAINT departement_nom_key UNIQUE (nom);


--
-- TOC entry 4748 (class 2606 OID 41015)
-- Name: departement departement_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.departement
    ADD CONSTRAINT departement_pkey PRIMARY KEY (id);


--
-- TOC entry 4756 (class 2606 OID 41049)
-- Name: etudiant etudiant_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.etudiant
    ADD CONSTRAINT etudiant_pkey PRIMARY KEY (id);


--
-- TOC entry 4764 (class 2606 OID 41091)
-- Name: examen examen_module_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.examen
    ADD CONSTRAINT examen_module_id_key UNIQUE (module_id);


--
-- TOC entry 4766 (class 2606 OID 41089)
-- Name: examen examen_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.examen
    ADD CONSTRAINT examen_pkey PRIMARY KEY (id);


--
-- TOC entry 4750 (class 2606 OID 41025)
-- Name: formation formation_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.formation
    ADD CONSTRAINT formation_pkey PRIMARY KEY (id);


--
-- TOC entry 4774 (class 2606 OID 41111)
-- Name: inscription inscription_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inscription
    ADD CONSTRAINT inscription_pkey PRIMARY KEY (etudiant_id, module_id);


--
-- TOC entry 4760 (class 2606 OID 41062)
-- Name: module module_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.module
    ADD CONSTRAINT module_pkey PRIMARY KEY (id);


--
-- TOC entry 4754 (class 2606 OID 41037)
-- Name: professeur professeur_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.professeur
    ADD CONSTRAINT professeur_pkey PRIMARY KEY (id);


--
-- TOC entry 4762 (class 2606 OID 41081)
-- Name: salle salle_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.salle
    ADD CONSTRAINT salle_pkey PRIMARY KEY (id);


--
-- TOC entry 4757 (class 1259 OID 41130)
-- Name: idx_etudiant_formation; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_etudiant_formation ON public.etudiant USING btree (formation_id);


--
-- TOC entry 4767 (class 1259 OID 41132)
-- Name: idx_examen_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_examen_date ON public.examen USING btree (date);


--
-- TOC entry 4768 (class 1259 OID 41135)
-- Name: idx_examen_module; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_examen_module ON public.examen USING btree (module_id);


--
-- TOC entry 4769 (class 1259 OID 41133)
-- Name: idx_examen_professeur; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_examen_professeur ON public.examen USING btree (professeur_id);


--
-- TOC entry 4770 (class 1259 OID 41134)
-- Name: idx_examen_salle; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_examen_salle ON public.examen USING btree (salle_id);


--
-- TOC entry 4751 (class 1259 OID 41128)
-- Name: idx_formation_departement; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_formation_departement ON public.formation USING btree (departement_id);


--
-- TOC entry 4771 (class 1259 OID 41136)
-- Name: idx_inscription_etudiant; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_inscription_etudiant ON public.inscription USING btree (etudiant_id);


--
-- TOC entry 4772 (class 1259 OID 41137)
-- Name: idx_inscription_module; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_inscription_module ON public.inscription USING btree (module_id);


--
-- TOC entry 4758 (class 1259 OID 41131)
-- Name: idx_module_formation; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_module_formation ON public.module USING btree (formation_id);


--
-- TOC entry 4752 (class 1259 OID 41129)
-- Name: idx_professeur_departement; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_professeur_departement ON public.professeur USING btree (departement_id);


--
-- TOC entry 4785 (class 2620 OID 41127)
-- Name: examen trg_exam_overlap; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_exam_overlap BEFORE INSERT OR UPDATE ON public.examen FOR EACH ROW EXECUTE FUNCTION public.check_exam_overlap();


--
-- TOC entry 4786 (class 2620 OID 41125)
-- Name: examen trg_professor_max_exams; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_professor_max_exams BEFORE INSERT OR UPDATE ON public.examen FOR EACH ROW EXECUTE FUNCTION public.check_professor_max_3_exams();


--
-- TOC entry 4787 (class 2620 OID 41123)
-- Name: examen trg_student_exam_per_day; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_student_exam_per_day BEFORE INSERT OR UPDATE ON public.examen FOR EACH ROW EXECUTE FUNCTION public.check_student_one_exam_per_day();


--
-- TOC entry 4777 (class 2606 OID 41050)
-- Name: etudiant fk_etudiant_formation; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.etudiant
    ADD CONSTRAINT fk_etudiant_formation FOREIGN KEY (formation_id) REFERENCES public.formation(id) ON DELETE CASCADE;


--
-- TOC entry 4780 (class 2606 OID 41092)
-- Name: examen fk_examen_module; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.examen
    ADD CONSTRAINT fk_examen_module FOREIGN KEY (module_id) REFERENCES public.module(id) ON DELETE CASCADE;


--
-- TOC entry 4781 (class 2606 OID 41097)
-- Name: examen fk_examen_professeur; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.examen
    ADD CONSTRAINT fk_examen_professeur FOREIGN KEY (professeur_id) REFERENCES public.professeur(id) ON DELETE RESTRICT;


--
-- TOC entry 4782 (class 2606 OID 41102)
-- Name: examen fk_examen_salle; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.examen
    ADD CONSTRAINT fk_examen_salle FOREIGN KEY (salle_id) REFERENCES public.salle(id) ON DELETE RESTRICT;


--
-- TOC entry 4775 (class 2606 OID 41026)
-- Name: formation fk_formation_departement; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.formation
    ADD CONSTRAINT fk_formation_departement FOREIGN KEY (departement_id) REFERENCES public.departement(id) ON DELETE CASCADE;


--
-- TOC entry 4783 (class 2606 OID 41112)
-- Name: inscription fk_inscription_etudiant; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inscription
    ADD CONSTRAINT fk_inscription_etudiant FOREIGN KEY (etudiant_id) REFERENCES public.etudiant(id) ON DELETE CASCADE;


--
-- TOC entry 4784 (class 2606 OID 41117)
-- Name: inscription fk_inscription_module; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inscription
    ADD CONSTRAINT fk_inscription_module FOREIGN KEY (module_id) REFERENCES public.module(id) ON DELETE CASCADE;


--
-- TOC entry 4778 (class 2606 OID 41063)
-- Name: module fk_module_formation; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.module
    ADD CONSTRAINT fk_module_formation FOREIGN KEY (formation_id) REFERENCES public.formation(id) ON DELETE CASCADE;


--
-- TOC entry 4779 (class 2606 OID 41068)
-- Name: module fk_module_prerequis; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.module
    ADD CONSTRAINT fk_module_prerequis FOREIGN KEY (pre_requis_id) REFERENCES public.module(id) ON DELETE SET NULL;


--
-- TOC entry 4776 (class 2606 OID 41038)
-- Name: professeur fk_professeur_departement; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.professeur
    ADD CONSTRAINT fk_professeur_departement FOREIGN KEY (departement_id) REFERENCES public.departement(id) ON DELETE CASCADE;


-- Completed on 2025-12-30 22:37:21

--
-- PostgreSQL database dump complete
--

