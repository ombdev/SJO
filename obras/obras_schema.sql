CREATE TABLE ent_project (
    id serial NOT NULL,
    title character varying NOT NULL,
    description character varying NOT NULL,
    city integer NOT NULL,
    category integer NOT NULL,
    bureau integer NOT NULL,
    budget double precision NOT NULL,
    contract integer NOT NULL,
    planed_kickoff date,
    planed_ending date,
    blocked boolean DEFAULT false,
    inception_time timestamp with time zone NOT NULL,
    touch_latter_time timestamp with time zone
);


COMMENT ON COLUMN ent_project.category IS 'Llave foranea a tabla de attributo categoria';
COMMENT ON COLUMN ent_project.contract IS 'Llave foranea a tabla de attributo contrato';
COMMENT ON COLUMN ent_project.bureau IS 'Llave foranea a table de attributo dependencia de gobierno';
COMMENT ON COLUMN ent_project.title IS 'Nombre con el que se identifica a este proyecto';
COMMENT ON COLUMN ent_project.planed_kickoff IS 'Fecha planeada para su inicio';
COMMENT ON COLUMN ent_project.planed_ending IS 'Fecha planeada para su conclusion';
COMMENT ON COLUMN ent_project.inception_time IS 'Fecha en la que se registro este proyecto';
COMMENT ON COLUMN ent_project.touch_latter_time IS 'Apunta a la ultima fecha de alteracion de el registro';
COMMENT ON COLUMN ent_project.blocked IS 'Implementacion de feature borrado logico';


CREATE FUNCTION obra_edit(
    _obra_id integer,
    _titulo character varying,
    _status integer,
    _municipio integer,
    _categoria integer,
    _monto double precision,
    _contrato character varying,
    _licitacion character varying
)
  RETURNS record AS
$BODY$

DECLARE

    current_moment timestamp with time zone = now();
    coincidences integer := 0;
    latter_id integer := 0;

    -- dump of errors
    rmsg text;

BEGIN

    CASE

        WHEN _obra_id = 0 THEN:

            -- :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
            -- STARTS - Validates clave unica
            --
            -- JUSTIFICATION: Clave unica is created by another division
            -- We should only abide with the format
            -- :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

            -- pending implementation

            -- :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
            -- ENDS   - Validates clave_unica
            -- :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

            INSERT INTO ent_project (
                control,
                titulo,
                status,
                municipio,
                categoria,
                monto,
                contrato,
                licitacion,
                momento_alta
            ) VALUES (
                clave_unica,
                _titulo,
                _status,
                _municipio,
                _categoria,
                _monto,
                _contrato,
                _licitacion,
                current_moment
            ) RETURNING id INTO latter_id;

        WHEN _obra_id > 0 THEN

            -- :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
            -- STARTS - Validates obra id
            --
            -- JUSTIFICATION: Because UPDATE statement does not issue
            -- any exception if nothing was updated.
            -- :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
            SELECT count(id)
            FROM obras INTO coincidences;
            WHERE not borrado_logico AND id = _obra_id;

            IF not coincidences = 1 THEN
                RAISE EXCEPTION 'obra identifier % does not exist', _obra_id;
            ENDIF;
            -- :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
            -- ENDS - Validate obra id
            -- :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

            UPDATE ent_project
            SET titulo = _titulo, status = _status,
                municipio = _municipio, categoria = _categoria,
                monto = _monto, contrato = _contrato,
                licitacion = _licitacion,
                momento_ultima_actualizacion = current_moment
            WHERE id = _obra_id;

            -- Upon edition we return obra id as latter id
            latter_id = _obra_id;

        ELSE
            RAISE EXCEPTION 'negative obra identifier % is unsupported', _obra_id;

    END CASE;

    return ( latter_id::integer, ''::text );

    EXCEPTION
        WHEN OTHERS THEN
            GET STACKED DIAGNOSTICS rmsg = MESSAGE_TEXT;
            return ( -1::integer, rmsg::text );

    RETURN rv;

END;
$BODY$
  LANGUAGE plpgsql VOLATILE COST 100;
