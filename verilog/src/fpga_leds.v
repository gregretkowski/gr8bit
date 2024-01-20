// Implements the LEDs from CPU to FPGA

module fpga_leds (
    input clk,
    input zro,
    input run,
    input [0:7] status,
    output reg [5:0] led
);

always @(posedge clk) begin
    led[0] = run;
    led[1] = zro;
    led[2] = status[0];
    led[3] = status[1];
    led[4] = status[2];
    led[5] = status[3];
end

endmodule