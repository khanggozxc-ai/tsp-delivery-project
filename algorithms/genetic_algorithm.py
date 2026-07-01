from __future__ import annotations

import random
from time import perf_counter
from typing import Any

import numpy as np

from services.distance_service import calculate_route_distance


def _validate_parameters(
    distance_matrix: np.ndarray,
    start_index: int,
    population_size: int,
    generations: int,
    crossover_rate: float,
    mutation_rate: float,
    tournament_size: int,
    elite_size: int,
) -> None:
    """Kiểm tra các tham số đầu vào của Genetic Algorithm."""

    location_count = len(distance_matrix)

    if location_count < 2:
        raise ValueError("Cần ít nhất hai địa điểm.")

    if start_index < 0 or start_index >= location_count:
        raise ValueError("Điểm xuất phát không hợp lệ.")

    if population_size < 2:
        raise ValueError("Kích thước quần thể phải từ 2 trở lên.")

    if generations < 1:
        raise ValueError("Số thế hệ phải từ 1 trở lên.")

    if not 0 <= crossover_rate <= 1:
        raise ValueError("Tỷ lệ lai ghép phải nằm trong khoảng 0 đến 1.")

    if not 0 <= mutation_rate <= 1:
        raise ValueError("Tỷ lệ đột biến phải nằm trong khoảng 0 đến 1.")

    if tournament_size < 2:
        raise ValueError("Tournament size phải từ 2 trở lên.")

    if tournament_size > population_size:
        raise ValueError(
            "Tournament size không được lớn hơn kích thước quần thể."
        )

    if elite_size < 0:
        raise ValueError("Elite size không được âm.")

    if elite_size >= population_size:
        raise ValueError(
            "Elite size phải nhỏ hơn kích thước quần thể."
        )


def _build_full_route(
    chromosome: list[int],
    start_index: int,
) -> list[int]:
    """
    Ghép điểm xuất phát với nhiễm sắc thể.

    Ví dụ:
    start_index = 0
    chromosome = [3, 1, 2]

    Kết quả:
    [0, 3, 1, 2]
    """

    return [start_index, *chromosome]


def _calculate_chromosome_distance(
    chromosome: list[int],
    distance_matrix: np.ndarray,
    start_index: int,
    return_to_start: bool,
) -> float:
    """Tính tổng khoảng cách của một cá thể."""

    route = _build_full_route(
        chromosome=chromosome,
        start_index=start_index,
    )

    return calculate_route_distance(
        route=route,
        distance_matrix=distance_matrix,
        return_to_start=return_to_start,
    )


def _create_initial_population(
    genes: list[int],
    population_size: int,
    random_generator: random.Random,
) -> list[list[int]]:
    """
    Sinh quần thể ban đầu.

    Mỗi cá thể là một hoán vị của các địa điểm,
    không chứa điểm xuất phát.
    """

    population: list[list[int]] = []

    for _ in range(population_size):
        chromosome = random_generator.sample(
            genes,
            k=len(genes),
        )
        population.append(chromosome)

    return population


def _tournament_selection(
    population: list[list[int]],
    distances: list[float],
    tournament_size: int,
    random_generator: random.Random,
) -> list[int]:
    """
    Chọn một cá thể bằng Tournament Selection.

    Chọn ngẫu nhiên một nhóm cá thể, sau đó lấy cá thể
    có tổng khoảng cách nhỏ nhất.
    """

    candidate_indices = random_generator.sample(
        range(len(population)),
        k=tournament_size,
    )

    winner_index = min(
        candidate_indices,
        key=lambda index: distances[index],
    )

    return population[winner_index].copy()


def _ordered_crossover(
    parent_1: list[int],
    parent_2: list[int],
    random_generator: random.Random,
) -> list[int]:
    """
    Ordered Crossover — OX.

    Phương pháp này bảo đảm mỗi địa điểm chỉ xuất hiện một lần.
    """

    chromosome_length = len(parent_1)

    if chromosome_length < 2:
        return parent_1.copy()

    start_position, end_position = sorted(
        random_generator.sample(
            range(chromosome_length),
            k=2,
        )
    )

    child: list[int | None] = [None] * chromosome_length

    # Sao chép một đoạn từ cha/mẹ thứ nhất.
    child[start_position : end_position + 1] = (
        parent_1[start_position : end_position + 1]
    )

    # Lấy các gen còn thiếu theo thứ tự của cha/mẹ thứ hai.
    remaining_genes = [
        gene
        for gene in parent_2
        if gene not in child
    ]

    insertion_positions = (
        list(range(end_position + 1, chromosome_length))
        + list(range(0, start_position))
    )

    for position, gene in zip(
        insertion_positions,
        remaining_genes,
    ):
        child[position] = gene

    return [int(gene) for gene in child]


def _mutate(
    chromosome: list[int],
    mutation_rate: float,
    random_generator: random.Random,
) -> list[int]:
    """
    Đột biến một cá thể.

    Ngẫu nhiên chọn một trong hai cách:
    - Swap Mutation: đổi chỗ hai địa điểm.
    - Inversion Mutation: đảo ngược một đoạn.
    """

    mutated = chromosome.copy()

    if len(mutated) < 2:
        return mutated

    if random_generator.random() >= mutation_rate:
        return mutated

    position_1, position_2 = sorted(
        random_generator.sample(
            range(len(mutated)),
            k=2,
        )
    )

    if random_generator.random() < 0.5:
        # Swap Mutation
        mutated[position_1], mutated[position_2] = (
            mutated[position_2],
            mutated[position_1],
        )
    else:
        # Inversion Mutation
        mutated[position_1 : position_2 + 1] = reversed(
            mutated[position_1 : position_2 + 1]
        )

    return mutated


def solve_genetic_algorithm(
    distance_matrix: np.ndarray,
    start_index: int = 0,
    return_to_start: bool = True,
    population_size: int = 100,
    generations: int = 300,
    crossover_rate: float = 0.8,
    mutation_rate: float = 0.05,
    tournament_size: int = 5,
    elite_size: int = 2,
    random_seed: int | None = None,
) -> dict[str, Any]:
    """
    Giải bài toán TSP bằng Genetic Algorithm.

    Điểm xuất phát được cố định.
    Các cá thể chỉ chứa thứ tự của những địa điểm còn lại.
    """

    _validate_parameters(
        distance_matrix=distance_matrix,
        start_index=start_index,
        population_size=population_size,
        generations=generations,
        crossover_rate=crossover_rate,
        mutation_rate=mutation_rate,
        tournament_size=tournament_size,
        elite_size=elite_size,
    )

    random_generator = random.Random(random_seed)

    location_count = len(distance_matrix)

    genes = [
        index
        for index in range(location_count)
        if index != start_index
    ]

    population = _create_initial_population(
        genes=genes,
        population_size=population_size,
        random_generator=random_generator,
    )

    best_chromosome: list[int] | None = None
    best_distance = float("inf")

    # Lưu khoảng cách tốt nhất qua từng thế hệ.
    history: list[float] = []

    start_time = perf_counter()

    for generation_index in range(generations):
        distances = [
            _calculate_chromosome_distance(
                chromosome=chromosome,
                distance_matrix=distance_matrix,
                start_index=start_index,
                return_to_start=return_to_start,
            )
            for chromosome in population
        ]

        sorted_indices = sorted(
            range(len(population)),
            key=lambda index: distances[index],
        )

        generation_best_index = sorted_indices[0]
        generation_best_distance = distances[generation_best_index]

        if generation_best_distance < best_distance:
            best_distance = generation_best_distance
            best_chromosome = population[
                generation_best_index
            ].copy()

        history.append(best_distance)

        # Không cần sinh quần thể mới sau thế hệ cuối.
        if generation_index == generations - 1:
            break

        next_population: list[list[int]] = []

        # Elitism: giữ lại một số cá thể tốt nhất.
        for index in sorted_indices[:elite_size]:
            next_population.append(
                population[index].copy()
            )

        while len(next_population) < population_size:
            parent_1 = _tournament_selection(
                population=population,
                distances=distances,
                tournament_size=tournament_size,
                random_generator=random_generator,
            )

            parent_2 = _tournament_selection(
                population=population,
                distances=distances,
                tournament_size=tournament_size,
                random_generator=random_generator,
            )

            if random_generator.random() < crossover_rate:
                child_1 = _ordered_crossover(
                    parent_1=parent_1,
                    parent_2=parent_2,
                    random_generator=random_generator,
                )

                child_2 = _ordered_crossover(
                    parent_1=parent_2,
                    parent_2=parent_1,
                    random_generator=random_generator,
                )
            else:
                child_1 = parent_1.copy()
                child_2 = parent_2.copy()

            child_1 = _mutate(
                chromosome=child_1,
                mutation_rate=mutation_rate,
                random_generator=random_generator,
            )

            child_2 = _mutate(
                chromosome=child_2,
                mutation_rate=mutation_rate,
                random_generator=random_generator,
            )

            next_population.append(child_1)

            if len(next_population) < population_size:
                next_population.append(child_2)

        population = next_population

    execution_time = perf_counter() - start_time

    if best_chromosome is None:
        raise RuntimeError(
            "Genetic Algorithm không tìm được lộ trình."
        )

    best_route = _build_full_route(
        chromosome=best_chromosome,
        start_index=start_index,
    )

    display_route = best_route.copy()

    if return_to_start:
        display_route.append(start_index)

    return {
        "algorithm": "Genetic Algorithm",
        "route": best_route,
        "display_route": display_route,
        "distance": float(best_distance),
        "execution_time": execution_time,
        "evaluated_routes": population_size * generations,
        "return_to_start": return_to_start,
        "history": history,
        "generation_count": generations,
        "parameters": {
            "population_size": population_size,
            "generations": generations,
            "crossover_rate": crossover_rate,
            "mutation_rate": mutation_rate,
            "tournament_size": tournament_size,
            "elite_size": elite_size,
            "random_seed": random_seed,
        },
    }