from flask_restplus import fields

from genl.restplus import api
from misc.helperpg import EmptySetError

from .entity import (MultipleResultsFound, NoResultFound, count_entities,
                     delete_entity, find_entity, page_entities)
from .helper import exec_steady, run_store_procedure

model = api.model(
    "Project Model",
    {
        "id": fields.Integer(required=True, description="Unique identifier"),
        "title": fields.String(required=True, description="Project name"),
        "description": fields.String(
            required=True, description="Short description of the project"
        ),
        "city": fields.Integer(required=True, description="DB id of the city"),
        "category": fields.Integer(required=True, description="DB id of the category"),
        "department": fields.Integer(
            required=True, description="DB id of the department"
        ),
        "budget": fields.Integer(required=True, description="DB id of the budget"),
        "contract": fields.Integer(required=True, description="DB id of the contract"),
        "planed_kickoff": fields.Date(
            required=True, description="When the project is planned to start"
        ),
        "planed_ending": fields.Date(
            required=True, description="When the project is planned to end"
        ),
        "inceptor_uuid": fields.String(
            required=True, description="UUID of the user who created the project"
        ),
    },
)


def _alter_project(**kwargs):
    """Calls sp in charge of create and edit a project"""
    sql = """select * from alter_project(
        {}::integer,
        '{}'::character varying,
        '{}'::text,
        {}::integer,
        {}::integer,
        {}::integer,
        {}::integer,
        {}::double precision,
        '{}'::date,
        '{}'::date,
        '{}'::character varying)
    AS result( rc integer, msg text )""".format(
        kwargs["id"],
        kwargs["title"],
        kwargs["description"],
        kwargs["city"],
        kwargs["category"],
        kwargs["department"],
        kwargs["contract"],
        kwargs["budget"],
        kwargs["planed_kickoff"],
        kwargs["planed_ending"],
        kwargs["inceptor_uuid"],
    )
    return run_store_procedure(sql)


def _setup_search_criteria(search_params):
    filters = {
        "project": "projects.id",
        "contract_number": "contracts.id",
        "contract": "contracts.id",
        "category": "categories.id",
    }

    if search_params is not None:
        criteria = []
        for field, value in search_params.items():
            criteria.append(f"{filters[field]} = {value}")

        search = " AND " + " AND ".join(criteria)
    else:
        search = ""

    return search


def paged_with_follow_ups(offset=0, limit=10, search_params=None):
    sql = """
    SELECT
        distinct(projects.id),
        projects.id,
        projects.title,
        projects.city AS city_id,
        contracts.number AS contract_number,
        departments.title AS department,
        departments.id AS department_id,
        categories.title AS category,
        categories.id AS category_id,
        follow_ups.verified_progress,
        follow_ups.check_stage,
        follow_ups.check_date
    FROM projects
    JOIN contracts ON contracts.id = projects.contract
    JOIN categories ON categories.id = projects.category
    JOIN departments ON departments.id = projects.department
    LEFT JOIN follow_ups ON follow_ups.project = projects.id
    WHERE projects.blocked = false {}
    ORDER BY follow_ups.check_stage
    OFFSET {} LIMIT {};
    """

    search = _setup_search_criteria(search_params)
    print(search)
    sql = sql.format(search, offset, limit)

    try:
        rows = exec_steady(sql)
    except EmptySetError:
        return []

    entities = []
    for row in rows:
        entities.append(dict(row))

    return entities


def paged_with_follow_ups_count(search_params=None):
    sql = """
    SELECT
        distinct(projects.id),
        count(projects.id)::int as total,
        follow_ups.check_stage
    FROM projects
    JOIN contracts ON contracts.id = projects.contract
    JOIN categories ON categories.id = projects.category
    JOIN departments ON departments.id = projects.department
    LEFT JOIN follow_ups ON follow_ups.project = projects.id
    WHERE projects.blocked = false {}
    GROUP BY projects.id, follow_ups.check_stage
    ORDER BY follow_ups.check_stage
    """

    search = _setup_search_criteria(search_params)
    print(search)
    sql = sql.format(search)

    try:
        rows = exec_steady(sql)
    except EmptySetError:
        return 0

    # For this case we are just expecting one row
    if len(rows) == 0:
        raise NoResultFound("Just expecting one total as a result")
    elif len(rows) > 1:
        raise MultipleResultsFound("Just expecting one row as a result")

    return rows.pop()["total"]


def create(**kwargs):
    """Creates a project entity"""
    kwargs["id"] = 0
    return _alter_project(**kwargs)


def edit(**kwargs):
    """Edits the allowed properties of a project entity"""
    return _alter_project(**kwargs)


def block(project_id):
    """Logical deletion of a project entity"""
    delete_entity("projects", project_id)


def find(project_id):
    """Find a project as per id"""
    return find_entity("projects", project_id)


def count(search_params=None):
    """Number of non logical deleted projects"""
    return count_entities("projects", search_params)


def paged(offset, limit=10, order_by="id", order="asc", search_params=None):
    return page_entities("projects", offset, limit, order_by, order, search_params)
