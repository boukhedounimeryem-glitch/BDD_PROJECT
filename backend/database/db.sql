-- ========================================
-- Base de données complète pour la gestion d'examens
-- ========================================

-- DROP TABLES existantes si besoin
DROP TABLE IF EXISTS public.inscription CASCADE;
DROP TABLE IF EXISTS public.examen CASCADE;
DROP TABLE IF EXISTS public.etudiant CASCADE;
DROP TABLE IF EXISTS public.professeur CASCADE;
DROP TABLE IF EXISTS public.module CASCADE;
DROP TABLE IF EXISTS public.formation CASCADE;
DROP TABLE IF EXISTS public.departement CASCADE;
DROP TABLE IF EXISTS public.salle CASCADE;
DROP TABLE IF EXISTS public.utilisateur CASCADE;

-- DROP SEQUENCES existantes si besoin
DROP SEQUENCE IF EXISTS public.departement_id_seq CASCADE;
DROP SEQUENCE IF EXISTS public.formation_id_seq CASCADE;
DROP SEQUENCE IF EXISTS public.module_id_seq CASCADE;
DROP SEQUENCE IF EXISTS public.professeur_id_seq CASCADE;
DROP SEQUENCE IF EXISTS public.etudiant_id_seq CASCADE;
DROP SEQUENCE IF EXISTS public.salle_id_seq CASCADE;
DROP SEQUENCE IF EXISTS public.examen_id_seq CASCADE;
DROP SEQUENCE IF EXISTS public.utilisateur_id_seq CASCADE;

-- =========================
-- SEQUENCES
-- =========================
CREATE SEQUENCE public.departement_id_seq START WITH 1;
CREATE SEQUENCE public.formation_id_seq START WITH 1;
CREATE SEQUENCE public.module_id_seq START WITH 1;
CREATE SEQUENCE public.professeur_id_seq START WITH 1;
CREATE SEQUENCE public.etudiant_id_seq START WITH 1;
CREATE SEQUENCE public.salle_id_seq START WITH 1;
CREATE SEQUENCE public.examen_id_seq START WITH 1;
CREATE SEQUENCE public.utilisateur_id_seq START WITH 1;

-- =========================
-- TABLES
-- =========================
CREATE TABLE public.departement (
    id integer NOT NULL DEFAULT nextval('public.departement_id_seq'::regclass),
    nom character varying(100) NOT NULL,
    CONSTRAINT departement_pkey PRIMARY KEY (id),
    CONSTRAINT departement_nom_key UNIQUE (nom)
);

CREATE TABLE public.formation (
    id integer NOT NULL DEFAULT nextval('public.formation_id_seq'::regclass),
    nom character varying(100) NOT NULL,
    niveau character varying(50) NOT NULL,
    nb_modules integer NOT NULL CHECK (nb_modules > 0),
    departement_id integer NOT NULL,
    CONSTRAINT formation_pkey PRIMARY KEY (id),
    CONSTRAINT fk_formation_departement FOREIGN KEY (departement_id) REFERENCES public.departement(id) ON DELETE CASCADE
);

CREATE TABLE public.module (
    id integer NOT NULL DEFAULT nextval('public.module_id_seq'::regclass),
    nom character varying(100) NOT NULL,
    credits integer NOT NULL CHECK (credits > 0),
    formation_id integer NOT NULL,
    pre_requis_id integer,
    CONSTRAINT module_pkey PRIMARY KEY (id),
    CONSTRAINT fk_module_formation FOREIGN KEY (formation_id) REFERENCES public.formation(id) ON DELETE CASCADE,
    CONSTRAINT fk_module_prerequis FOREIGN KEY (pre_requis_id) REFERENCES public.module(id) ON DELETE SET NULL
);

CREATE TABLE public.professeur (
    id integer NOT NULL DEFAULT nextval('public.professeur_id_seq'::regclass),
    nom character varying(100) NOT NULL,
    specialite character varying(100),
    departement_id integer NOT NULL,
    CONSTRAINT professeur_pkey PRIMARY KEY (id),
    CONSTRAINT fk_professeur_departement FOREIGN KEY (departement_id) REFERENCES public.departement(id) ON DELETE CASCADE
);

CREATE TABLE public.etudiant (
    id integer NOT NULL DEFAULT nextval('public.etudiant_id_seq'::regclass),
    nom character varying(100) NOT NULL,
    prenom character varying(100) NOT NULL,
    promotion integer NOT NULL,
    formation_id integer NOT NULL,
    CONSTRAINT etudiant_pkey PRIMARY KEY (id),
    CONSTRAINT fk_etudiant_formation FOREIGN KEY (formation_id) REFERENCES public.formation(id) ON DELETE CASCADE
);

CREATE TABLE public.salle (
    id integer NOT NULL DEFAULT nextval('public.salle_id_seq'::regclass),
    nom character varying(100) NOT NULL,
    capacite integer NOT NULL CHECK (capacite > 0),
    type character varying(20) NOT NULL CHECK (type IN ('amphi','salle')),
    batiment character varying(100) NOT NULL,
    CONSTRAINT salle_pkey PRIMARY KEY (id)
);

CREATE TABLE public.examen (
    id integer NOT NULL DEFAULT nextval('public.examen_id_seq'::regclass),
    date date NOT NULL,
    heure_debut time NOT NULL,
    duree_minutes integer NOT NULL CHECK (duree_minutes > 0),
    module_id integer NOT NULL UNIQUE,
    professeur_id integer NOT NULL,
    salle_id integer NOT NULL,
    CONSTRAINT examen_pkey PRIMARY KEY (id),
    CONSTRAINT fk_examen_module FOREIGN KEY (module_id) REFERENCES public.module(id) ON DELETE CASCADE,
    CONSTRAINT fk_examen_professeur FOREIGN KEY (professeur_id) REFERENCES public.professeur(id) ON DELETE RESTRICT,
    CONSTRAINT fk_examen_salle FOREIGN KEY (salle_id) REFERENCES public.salle(id) ON DELETE RESTRICT
);

CREATE TABLE public.inscription (
    etudiant_id integer NOT NULL,
    module_id integer NOT NULL,
    note double precision,
    CONSTRAINT inscription_pkey PRIMARY KEY (etudiant_id,module_id),
    CONSTRAINT fk_inscription_etudiant FOREIGN KEY (etudiant_id) REFERENCES public.etudiant(id) ON DELETE CASCADE,
    CONSTRAINT fk_inscription_module FOREIGN KEY (module_id) REFERENCES public.module(id) ON DELETE CASCADE
);

CREATE TABLE public.utilisateur (
    id integer NOT NULL DEFAULT nextval('public.utilisateur_id_seq'::regclass),
    login character varying(100) NOT NULL,
    password_hash text NOT NULL,
    role character varying(20) NOT NULL CHECK (role IN ('admin','prof','etudiant')),
    professeur_id integer,
    etudiant_id integer,
    CONSTRAINT utilisateur_pkey PRIMARY KEY (id),
    CONSTRAINT utilisateur_login_key UNIQUE (login),
    CONSTRAINT fk_utilisateur_professeur FOREIGN KEY (professeur_id) REFERENCES public.professeur(id) ON DELETE SET NULL,
    CONSTRAINT fk_utilisateur_etudiant FOREIGN KEY (etudiant_id) REFERENCES public.etudiant(id) ON DELETE SET NULL,
    CONSTRAINT ck_utilisateur_role_link CHECK (
        (role = 'admin' AND professeur_id IS NULL AND etudiant_id IS NULL)
        OR (role = 'prof' AND professeur_id IS NOT NULL AND etudiant_id IS NULL)
        OR (role = 'etudiant' AND etudiant_id IS NOT NULL AND professeur_id IS NULL)
    )
);

-- =========================
-- TRIGGERS pour contraintes métiers
-- =========================
-- 1) Chevauchement salle
CREATE OR REPLACE FUNCTION public.check_exam_overlap() RETURNS trigger LANGUAGE plpgsql AS $$
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
CREATE TRIGGER trg_exam_overlap BEFORE INSERT OR UPDATE ON public.examen FOR EACH ROW EXECUTE FUNCTION public.check_exam_overlap();

-- 2) Max 3 examens par professeur par jour
CREATE OR REPLACE FUNCTION public.check_professor_max_3_exams() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF (
        SELECT COUNT(*) FROM examen WHERE professeur_id = NEW.professeur_id AND date = NEW.date
    ) >= 3 THEN
        RAISE EXCEPTION 'Un professeur ne peut pas surveiller plus de 3 examens par jour';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER trg_professor_max_exams BEFORE INSERT OR UPDATE ON public.examen FOR EACH ROW EXECUTE FUNCTION public.check_professor_max_3_exams();

-- 3) 1 examen par jour par étudiant
CREATE OR REPLACE FUNCTION public.check_student_one_exam_per_day() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM inscription i
        JOIN examen e ON e.module_id = i.module_id
        WHERE i.etudiant_id IN (
            SELECT etudiant_id FROM inscription WHERE module_id = NEW.module_id
        )
        AND e.date = NEW.date
        AND e.id <> NEW.id
    ) THEN
        RAISE EXCEPTION 'Un étudiant ne peut pas avoir plus d''un examen par jour';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER trg_student_exam_per_day BEFORE INSERT OR UPDATE ON public.examen FOR EACH ROW EXECUTE FUNCTION public.check_student_one_exam_per_day();

-- =========================
-- INSERTS
-- =========================

-- Départements
INSERT INTO public.departement (nom) VALUES
('Informatique'), ('Mathématiques'), ('Physique'), ('Gestion');

-- Formations
INSERT INTO public.formation (nom,niveau,nb_modules,departement_id) VALUES
('Licence Info 1','L1',5,1),('Licence Info 2','L2',6,1),('Licence Info 3','L3',6,1),
('Master Info 1','M1',5,1),('Master Info 2','M2',4,1),
('Licence Math 3','L3',5,2),('Master Math 1','M1',4,2),
('Licence Physique 3','L3',5,3),('Licence Gestion 3','L3',5,4);

-- Modules
INSERT INTO public.module (nom,credits,formation_id,pre_requis_id) VALUES
('Algèbre 1',6,6,NULL),('Analyse 1',6,6,NULL),('Probabilités',6,6,NULL),
('Statistiques',6,7,NULL),('Analyse avancée',6,7,2),
('Programmation Python',6,3,NULL),('Bases de données',6,3,NULL),('Réseaux informatiques',6,3,NULL),
('Systèmes d''exploitation',6,3,NULL),('Développement web',6,3,NULL),
('Intelligence artificielle',6,4,6),('Big Data',6,4,7),
('Mécanique quantique',6,8,NULL),('Électromagnétisme',6,8,NULL),
('Gestion de projet',4,9,NULL);

-- Salles
INSERT INTO public.salle (nom,capacite,type,batiment) VALUES
('Amphi C',400,'amphi','Bloc C'),('Amphi D',350,'amphi','Bloc D'),
('Salle B2',30,'salle','Bloc B'),('Salle B3',25,'salle','Bloc B'),
('Salle C1',40,'salle','Bloc C'),('Salle D1',50,'salle','Bloc D');

-- Professeurs (50)
INSERT INTO public.professeur (nom,specialite,departement_id) VALUES
('Dr Prof1','Spécialité 1',1),('Dr Prof2','Spécialité 2',1),('Dr Prof3','Spécialité 3',1),
('Dr Prof4','Spécialité 4',2),('Dr Prof5','Spécialité 5',2),('Dr Prof6','Spécialité 6',2),
('Dr Prof7','Spécialité 7',3),('Dr Prof8','Spécialité 8',3),('Dr Prof9','Spécialité 9',3),
('Dr Prof10','Spécialité 10',4),('Dr Prof11','Spécialité 11',1),('Dr Prof12','Spécialité 12',1),
('Dr Prof13','Spécialité 13',2),('Dr Prof14','Spécialité 14',2),('Dr Prof15','Spécialité 15',3),
('Dr Prof16','Spécialité 16',3),('Dr Prof17','Spécialité 17',4),('Dr Prof18','Spécialité 18',4),
('Dr Prof19','Spécialité 19',1),('Dr Prof20','Spécialité 20',2),('Dr Prof21','Spécialité 21',3),
('Dr Prof22','Spécialité 22',4),('Dr Prof23','Spécialité 23',1),('Dr Prof24','Spécialité 24',2),
('Dr Prof25','Spécialité 25',3),('Dr Prof26','Spécialité 26',4),('Dr Prof27','Spécialité 27',1),
('Dr Prof28','Spécialité 28',2),('Dr Prof29','Spécialité 29',3),('Dr Prof30','Spécialité 30',4),
('Dr Prof31','Spécialité 31',1),('Dr Prof32','Spécialité 32',2),('Dr Prof33','Spécialité 33',3),
('Dr Prof34','Spécialité 34',4),('Dr Prof35','Spécialité 35',1),('Dr Prof36','Spécialité 36',2),
('Dr Prof37','Spécialité 37',3),('Dr Prof38','Spécialité 38',4),('Dr Prof39','Spécialité 39',1),
('Dr Prof40','Spécialité 40',2),('Dr Prof41','Spécialité 41',3),('Dr Prof42','Spécialité 42',4),
('Dr Prof43','Spécialité 43',1),('Dr Prof44','Spécialité 44',2),('Dr Prof45','Spécialité 45',3),
('Dr Prof46','Spécialité 46',4),('Dr Prof47','Spécialité 47',1),('Dr Prof48','Spécialité 48',2),
('Dr Prof49','Spécialité 49',3),('Dr Prof50','Spécialité 50',4);

-- Étudiants (100)
INSERT INTO public.etudiant (nom,prenom,promotion,formation_id) 
VALUES 
-- Etudiants 1 à 50
('Etudiant1','Prenom1',2023,1),('Etudiant2','Prenom2',2023,1),('Etudiant3','Prenom3',2023,2),
('Etudiant4','Prenom4',2023,2),('Etudiant5','Prenom5',2023,3),('Etudiant6','Prenom6',2023,3),
('Etudiant7','Prenom7',2023,1),('Etudiant8','Prenom8',2023,1),('Etudiant9','Prenom9',2023,2),
('Etudiant10','Prenom10',2023,2),('Etudiant11','Prenom11',2023,3),('Etudiant12','Prenom12',2023,3),
('Etudiant13','Prenom13',2023,1),('Etudiant14','Prenom14',2023,2),('Etudiant15','Prenom15',2023,3),
('Etudiant16','Prenom16',2023,4),('Etudiant17','Prenom17',2023,1),('Etudiant18','Prenom18',2023,2),
('Etudiant19','Prenom19',2023,3),('Etudiant20','Prenom20',2023,4),
('Etudiant21','Prenom21',2023,1),('Etudiant22','Prenom22',2023,2),('Etudiant23','Prenom23',2023,3),
('Etudiant24','Prenom24',2023,4),('Etudiant25','Prenom25',2023,1),
('Etudiant26','Prenom26',2023,2),('Etudiant27','Prenom27',2023,3),('Etudiant28','Prenom28',2023,4),
('Etudiant29','Prenom29',2023,1),('Etudiant30','Prenom30',2023,2),('Etudiant31','Prenom31',2023,3),
('Etudiant32','Prenom32',2023,4),('Etudiant33','Prenom33',2023,1),('Etudiant34','Prenom34',2023,2),
('Etudiant35','Prenom35',2023,3),('Etudiant36','Prenom36',2023,4),('Etudiant37','Prenom37',2023,1),
('Etudiant38','Prenom38',2023,2),('Etudiant39','Prenom39',2023,3),('Etudiant40','Prenom40',2023,4),
('Etudiant41','Prenom41',2023,1),('Etudiant42','Prenom42',2023,2),('Etudiant43','Prenom43',2023,3),
('Etudiant44','Prenom44',2023,4),('Etudiant45','Prenom45',2023,1),('Etudiant46','Prenom46',2023,2),
('Etudiant47','Prenom47',2023,3),('Etudiant48','Prenom48',2023,4),('Etudiant49','Prenom49',2023,1),
('Etudiant50','Prenom50',2023,2);

-- Synchronisation des séquences
SELECT setval('public.professeur_id_seq', (SELECT MAX(id) FROM public.professeur), true);
SELECT setval('public.etudiant_id_seq', (SELECT MAX(id) FROM public.etudiant), true);
