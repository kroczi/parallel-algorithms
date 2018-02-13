@everywhere using DistributedArrays
using Plots

function fill(i, j, size)
    if i == 1
        return (j - 1) / (size - 1)
    elseif i == size
        return ((j - 1) / (size - 1))^2
    elseif j == 1
        return 0
    elseif j == size
        return 1
    else
        return 0
    end
end

@everywhere function dampness_tile(old, x_start, x_end, y_start, y_end)
    m, n = size(old)
    new = similar(old, m-2, n-2)
    
    for j = y_start:y_end
        for i = x_start:x_end
            new[i - 1, j - 1] = (old[i - 1, j] + old[i, j - 1] + old[i + 1, j] + old[i, j + 1]) / 4
        end
    end

    # Copy boundary conditions
    if x_start == 3
        for j = 2:n-1
            new[1, j - 1] = old[2, j]
        end
    end

    if x_end == m - 2
        for j = 2:n-1
            new[m - 2, j - 1] = old[m - 1, j]
        end
    end

    if y_start == 3
        for i = 2:m-1
            new[i - 1, 1] = old[i, 2]
        end
    end

    if y_end == n - 2
        for i = 2:n-1
            new[i - 1, n-2] = old[i, n - 1]
        end
    end

    return new
end

@everywhere function dampness(d::DArray)
    DArray(size(d), procs(d)) do I
        
        old = Array{Float64}(length(I[1])+2, length(I[2])+2)
        old[2:end-1, 2:end-1] = d[I[1], I[2]]

        # Copy boarders only if necessary
        x_start = 2
        x_end = length(I[1]) + 1
        y_start = 2
        y_end = length(I[2]) + 1
        
        if first(I[1]) == 1
            x_start = 3
        else
            top = first(I[1]) - 1
            old[1, 2:end-1] = d[top , I[2]]
        end

        if last(I[1]) == size(d, 1)
            x_end = length(I[1])
        else
            bottom = last(I[1]) + 1
            old[end, 2:end-1] = d[bottom, I[2]]
        end

        if first(I[2]) == 1
            y_start = 3
        else
            left = first(I[2]) - 1
            old[2:end-1, 1] = d[I[1], left]
        end

        if last(I[2]) == size(d, 2)
            y_end = length(I[2])
        else
            right = last(I[2]) + 1
            old[2:end-1, end] = d[I[1], right]
        end

        new = dampness_tile(old, x_start, x_end, y_start, y_end)
    end
end

function task(problem_size, iterations, procs, prepare_plot=false)
    DA = distribute([fill(i, j, problem_size) for i = 1:problem_size, j = 1:problem_size], procs = workers()[1:procs], dist = [1,procs])
    for i=1:iterations
        DA = dampness(DA)
    end

    if prepare_plot
        Plots.gr()
        Plots.heatmap(linspace(0, 1, problem_size), linspace(0, 1, problem_size), convert(Array{Float64}, DA))
    end
end

function batch()
    repeats = 4
    iterations = 100

    # dummy run for libraries set up
    task(100, 10, 4, false)
    println("size", "\t", "iterations", "\t", "workers", "\t", "repeat", "\t", "time")

    for workers in 2:-1:1
        for problem_size in [100, 500, 1000]
            for i in 1:repeats
                elapsed = @elapsed(task(problem_size, iterations, workers, false))
                println(problem_size, "\t", iterations, "\t", workers, "\t", i, "\t", elapsed)
            end
        end
    end
end

worker_procs = parse(Int, ARGS[1])
problem_size = parse(Int, ARGS[2])
iterations = parse(Int, ARGS[3])

# dummy run for libraries set up
task(100, 10, worker_procs, false)

elapsed = @elapsed(task(problem_size, iterations, worker_procs, false))
println(problem_size, "\t", iterations, "\t", worker_procs, "\t", elapsed)
