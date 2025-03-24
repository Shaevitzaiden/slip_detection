clear; clc; clear all; 

% define the folders we will use for this code aka train and test folder
train_folder = "C:/Users/18328/Desktop/onr_tact/converted_data_for_slip/train_folder";
test_folder = "C:/Users/18328/Desktop/onr_tact/converted_data_for_slip/test_folder";

% lets load the csv files we will be using 
train_files = dir(fullfile(train_folder, '*.csv'));
test_files = dir(fullfile(test_folder, '*.csv'));

%  check if the number of files we said we have matches 
if length(train_files) < 8 || length(test_files) < 2
    error("Expected 8 training files and 2 test files. Check again ")
end 

% Define the window and step size (this can be adjusted)

% number of samples per window 
window_size = 15;
% step size to slide the window
step_size = 5;

% Initialize training data 
X_train =  [];
y_train = [];

%  load and process the data 
for i = 1:8
    % load file 
    data = readtable(fullfile(train_folder,train_files(i).name));

    % extracting the time and sensor values 
    time = data.("Time_s_");
    % Extract sensors 1 -8
    sensor_values = table2array(data(:,2:9)); 

    % define slip condition (this will change after ground truth)
    % slip occurs if sensor 8 <0.6 (low pressure on Sensor 8)
    % or if any sensors 1-7 are > 0.5 (high pressure on other sensors)
    slip_labels = (data.Sensor8 <0.7) | any(sensor_values(:,1:7) > 0.6, 2);

    %  now we apply the moving window 
    num_samples = length(time);
        for j = 1:step_size:(num_samples-window_size+1)
            % extract window data 
            window_data = sensor_values(j:j+window_size-1,:);
            % majority class in window 
            window_label = mode(slip_labels(j:j+window_size-1));

            % compute window based features (mean, std, max, min)
            windo_features = [mean(window_data); std(window_data); max(window_data); min(window_data)];

            % store features and labels for training
            % flatten into row  
            X_train = [X_train; windo_features(:)'];
            y_train = [y_train;window_label];
        end 
end 

% train random forest 

num_trees = 100;
rfModel= TreeBagger(num_trees,X_train,y_train, 'Method', 'classification');

% load and process test data 
X_test = [];
y_test = [];
time_test = [];

for i = 1:2
    % load the file 
    data = readtable(fullfile(test_folder, test_files(i).name));

    % extract time and sensor values 
    time = data.("Time_s_");
    sensor_values = table2array(data(:,2:9));

    % defne slip condition for test data 
    slip_labels = (data.Sensor8 < 0.7) | any(sensor_values(:,1:7)> 0.6,2);

    % apply moving window 
    num_samples = length(time);
    for j = 1:step_size:(num_samples-window_size+1)
        % extract windowed data 
        window_data = sensor_values(j:j+window_size-1,:);
        window_label = mode(slip_labels(j:j+window_size-1));

        % compute window-based features (mean, std, max, min)
        window_features = [mean(window_data); std(window_data); max(window_data); min(window_data)];
        
        % store features, labels, and time for testing 
        X_test = [X_test; window_features(:)'];
        y_test = [y_test; window_label];
        % store the time for plotting 
        time_test =[time_test; time(j)];
    end
end

% test model on new data 
% get predicted slip values 
y_pred = str2double(predict(rfModel, X_test));

% calcualte accuracy 
accuracy = sum(y_pred == y_test)/ length(y_test)*100;
fprintf('Model accuracy: %.2f%%\n', accuracy);

%  save predictions to csv file 
results_table = table(time_test, y_test, y_pred, 'VariableNames', {'Time', 'Actual_Slip', 'Predicted_Slip'});
writetable(results_table,"predicted.csv");
fprintf('Predictions saved to predictions.csv\n');

% plot actual vs. predicted slip & save the plot 
figure;
hold on;
% light blue shading for actual slip regions 
area(time_test,y_test,'FaceColor',[0.7,0.9,1],'EdgeColor','none','FaceAlpha',0.5);
% Actual slip (blue circles)
plot(time_test,y_test,'bo-','MarkerSize',4,'DisplayName','Actual Slip')
plot(time_test, y_pred, 'r.-', 'MarkerSize', 10, 'DisplayName', 'Predicted Slip'); % Predicted slip (red dots)
xlabel('Time (s)');
ylabel('Slip Status (0 = No Slip, 1 = Slip)');
title('Moving Window Slip Detection');
legend;
grid on;
hold off;

saveas(gcf,'slip_detection_plot.png');
fprintf('Plot saved as slip_detection_plot.png\n');